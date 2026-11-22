import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app import models  # register relationships
from app.db.session import Base, get_db
from app.core.security import create_access_token
from app.models.block import Block
from app.models.game import Game
from app.models.notification import Notification
from app.models.team import Team
from app.models.team_invitation import TeamInvitation
from app.models.team_join_request import TeamJoinRequest, TeamJoinRequestStatus
from app.models.team_member import TeamMember
from app.models.user import User
from app.routers.team_invitation import router
from app.routers.team import router as teams_router

@compiles(BigInteger, 'sqlite')
def sqlite_bigint(type_, compiler, **kwargs): return 'INTEGER'

class InvitationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine, tables=[User.__table__, Game.__table__, Team.__table__, TeamMember.__table__, TeamJoinRequest.__table__, TeamInvitation.__table__, Block.__table__, Notification.__table__])
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.Session() as db:
            db.add_all([User(id=n, email=f'u{n}@example.test', username=f'user{n}') for n in range(1, 5)])
            db.add(Game(id=1, name='Game', genre='MOBA'))
            db.add(Team(id=1, name='Alpha', main_game_id=1, captain_id=1, max_members=2))
            db.add(TeamMember(team_id=1, user_id=1, role='CAPTAIN'))
            db.commit()
        app = FastAPI(); app.include_router(router); app.include_router(teams_router, prefix="/api")
        def db_override():
            db = self.Session()
            try: yield db
            finally: db.close()
        app.dependency_overrides[get_db] = db_override
        self.client = TestClient(app)
    def request(self, method, url, user=None, body=None):
        return self.client.request(method, url, headers={'Authorization': 'Bearer ' + create_access_token({'sub': str(user)})} if user else {}, json=body)
    def invite(self, target=2, sender=1):
        return self.request('POST','/api/team-invitations',sender,{'team_id':1,'user_id':target})
    def test_invite_accept_and_authorization(self):
        self.assertEqual(self.invite(sender=2).status_code,403)
        self.assertEqual(self.invite(sender=None).status_code,401)
        with self.Session() as db:
            db.add(TeamJoinRequest(team_id=1,user_id=2,status=TeamJoinRequestStatus.PENDING)); db.commit()
        response=self.invite(); self.assertEqual(response.status_code,201)
        invitation=response.json()['data']['id']
        self.assertEqual(self.invite().status_code,409)
        self.assertEqual(len(self.request('GET','/api/team-invitations/me',2).json()['data']),1)
        self.assertEqual(self.request('PATCH',f'/api/team-invitations/{invitation}',3,{'action':'accept'}).status_code,403)
        self.assertEqual(self.request('PATCH',f'/api/team-invitations/{invitation}',2,{'action':'accept'}).status_code,200)
        self.assertEqual(self.request('PATCH',f'/api/team-invitations/{invitation}',2,{'action':'accept'}).status_code,409)
        with self.Session() as db:
            self.assertIsNotNone(db.query(TeamMember).filter_by(team_id=1,user_id=2).first())
            self.assertEqual(db.query(Notification).count(),2)
            self.assertEqual(db.query(TeamJoinRequest).filter_by(team_id=1,user_id=2).first().status,TeamJoinRequestStatus.ACCEPTED)
    def test_my_teams_after_accept(self):
        self.assertEqual(self.request('GET','/api/teams/mine').status_code,401)
        self.assertEqual(self.request('GET','/api/teams/mine',2).json()['data'],[])
        invitation=self.invite().json()['data']['id']
        self.assertEqual(self.request('PATCH',f'/api/team-invitations/{invitation}',2,{'action':'accept'}).status_code,200)
        team=self.request('GET','/api/teams/mine',2).json()['data'][0]
        self.assertEqual((team['name'],team['role'],team['members']),('Alpha','member',2))
        captain=self.request('GET','/api/teams/mine',1).json()['data'][0]
        self.assertEqual(captain['role'],'captain')
        self.assertEqual(self.request('GET','/api/teams/mine',3).json()['data'],[])

    def test_reject_and_reinvite(self):
        invitation=self.invite().json()['data']['id']
        self.assertEqual(self.request('PATCH',f'/api/team-invitations/{invitation}',2,{'action':'reject'}).status_code,200)
        self.assertEqual(self.request('GET','/api/team-invitations/me',2).json()['data'],[])
        self.assertEqual(self.invite().status_code,201)
        with self.Session() as db: self.assertIsNone(db.query(TeamMember).filter_by(team_id=1,user_id=2).first())
    def test_team_full_at_accept(self):
        invitation=self.invite().json()['data']['id']
        with self.Session() as db: db.add(TeamMember(team_id=1,user_id=3,role='MEMBER')); db.commit()
        self.assertEqual(self.request('PATCH',f'/api/team-invitations/{invitation}',2,{'action':'accept'}).status_code,409)
        with self.Session() as db: self.assertIsNone(db.query(TeamMember).filter_by(team_id=1,user_id=2).first())
    def test_block_and_invalid_user(self):
        self.assertEqual(self.invite(target=99).status_code,404)
        self.assertEqual(self.invite(target=1).status_code,409)
        with self.Session() as db: db.add(Block(blocker_id=2,blocked_id=1)); db.commit()
        self.assertEqual(self.invite().status_code,403)
    def test_invalid_action(self):
        invitation=self.invite().json()['data']['id']
        self.assertEqual(self.request('PATCH',f'/api/team-invitations/{invitation}',2,{'action':'maybe'}).status_code,422)

if __name__ == '__main__': unittest.main()
