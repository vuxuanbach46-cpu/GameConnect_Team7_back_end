import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app import models
from app.core.security import create_access_token
from app.db.session import Base, get_db
from app.models.user import User
from app.models.game import Game
from app.models.notification import Notification
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_join_request import TeamJoinRequest
from app.models.team_feed_post import TeamFeedPost
from app.routers import team, team_join, team_feed

@compiles(BigInteger, 'sqlite')
def sqlite_bigint(type_, compiler, **kw): return 'INTEGER'

class TeamWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine, tables=[User.__table__, Game.__table__, Team.__table__, TeamMember.__table__, TeamJoinRequest.__table__, TeamFeedPost.__table__, Notification.__table__])
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.Session() as db:
            db.add_all([User(id=i, email=f'u{i}@test.invalid', username=f'user{i}') for i in range(1,4)])
            db.add(Game(id=1,name='Game',genre='MOBA')); db.commit()
        app = FastAPI(); app.include_router(team_join.router,prefix='/api'); app.include_router(team_feed.router); app.include_router(team.router,prefix='/api')
        def override():
            db=self.Session()
            try: yield db
            finally: db.close()
        app.dependency_overrides[get_db] = override; self.client = TestClient(app)
    def request(self, method, url, user=None, body=None):
        headers={'Authorization':'Bearer '+create_access_token({'sub':str(user)})} if user else {}
        return self.client.request(method,url,headers=headers,json=body)
    def create(self,mode='PUBLIC'):
        return self.request('POST','/api/teams',1,{'name':'Alpha','main_game_id':1,'max_members':4,'join_mode':mode})
    def test_create_join_feed_and_leave(self):
        self.assertEqual(self.create().status_code,201)
        self.assertEqual(self.request('GET','/api/teams/mine').status_code,401)
        self.assertEqual(self.request('POST','/api/teams/1/join',2,{}).status_code,200)
        mine=self.request('GET','/api/teams/mine',2).json()['data']; self.assertEqual(mine[0]['name'],'Alpha')
        self.assertEqual(self.request('GET','/api/teams/1/feed',3).status_code,403)
        self.assertEqual(self.request('POST','/api/teams/1/feed',2,{'type':'announcement','title':'A','content':'B'}).status_code,403)
        r=self.request('POST','/api/teams/1/feed',1,{'type':'announcement','title':'Thông báo','content':'Chào đội'}); self.assertEqual(r.status_code,201)
        feed=self.request('GET','/api/teams/1/feed',2).json()['data']; self.assertEqual(feed['posts'][0]['title'],'Thông báo')
        self.assertEqual(self.request('POST','/api/teams/1/leave',2,{}).status_code,200)
        self.assertEqual(self.request('GET','/api/teams/1/feed',2).status_code,403)
    def test_schedule_validation_and_anonymous_access(self):
        self.assertEqual(self.create().status_code,201)
        self.assertEqual(self.request('GET','/api/teams/1/feed').status_code,401)
        payload={'type':'schedule','title':'Tập luyện','content':'Cùng chơi','play_date':'2026-11-26','play_time':'20:30'}
        self.assertEqual(self.request('POST','/api/teams/1/feed',1,payload).status_code,201)
        post=self.request('GET','/api/teams/1/feed',1).json()['data']['posts'][0]
        self.assertEqual((post['playDate'],post['playTime']),('2026-11-26','20:30'))
        self.assertEqual(self.request('POST','/api/teams/1/feed',1,{**payload,'play_date':'not-a-date'}).status_code,422)

    def test_review_join_request_and_invalid_post(self):
        self.assertEqual(self.create('APPROVAL_REQUIRED').status_code,201)
        self.assertEqual(self.request('POST','/api/teams/1/join',2,{}).status_code,200)
        self.assertEqual(self.request('GET','/api/teams/1/join-requests',2).status_code,403)
        rows=self.request('GET','/api/teams/1/join-requests',1).json()['data']; self.assertEqual(len(rows),1)
        self.assertEqual(self.request('PATCH',f"/api/teams/1/join-requests/{rows[0]['id']}",1,{'status':'ACCEPTED'}).status_code,200)
        self.assertEqual(self.request('GET','/api/teams/1/feed',2).status_code,200)
        self.assertEqual(self.request('POST','/api/teams/1/feed',1,{'type':'schedule','title':'A','content':'B'}).status_code,422)
        self.assertEqual(self.request('POST','/api/teams/1/feed',1,{'type':'announcement','title':'  ','content':'B'}).status_code,422)

if __name__ == '__main__': unittest.main()
