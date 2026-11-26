import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.security import create_access_token
from app.db.session import Base, get_db
from app.models.user import User
from app.routers.admin_users import router

@compiles(BigInteger, 'sqlite')
def sqlite_bigint(type_, compiler, **kw): return 'INTEGER'

class AdminUsersFlowTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(engine, tables=[User.__table__])
        self.session = sessionmaker(bind=engine, expire_on_commit=False)
        with self.session() as db:
            db.add_all([User(id=1, username='admin', email='admin@test.invalid', role='ADMIN'), User(id=2, username='player', email='player@test.invalid', role='USER')]); db.commit()
        app = FastAPI(); app.include_router(router)
        def override():
            db = self.session()
            try: yield db
            finally: db.close()
        app.dependency_overrides[get_db] = override
        self.client = TestClient(app)
    def request(self, method, path, user=None, **kwargs):
        headers = {'Authorization': 'Bearer ' + create_access_token({'sub': str(user)})} if user else {}
        return self.client.request(method, path, headers=headers, **kwargs)
    def test_auth_search_detail(self):
        self.assertEqual(self.request('GET', '/api/admin/users').status_code, 401)
        self.assertEqual(self.request('GET', '/api/admin/users', 2).status_code, 403)
        data = self.request('GET', '/api/admin/users?search=player&page=1&page_size=5', 1).json()['data']
        self.assertEqual((data['total'], data['items'][0]['username']), (1, 'player'))
        self.assertEqual(self.request('GET', '/api/admin/users/999', 1).status_code, 404)
    def test_lock_unlock_validation(self):
        path = '/api/admin/users/2'
        self.assertEqual(self.request('PATCH', path + '/lock', 1, json={'duration_days': 1, 'reason': ' '}).status_code, 422)
        self.assertEqual(self.request('PATCH', '/api/admin/users/1/lock', 1, json={'duration_days': 1, 'reason': 'test'}).status_code, 400)
        result = self.request('PATCH', path + '/lock', 1, json={'duration_days': None, 'reason': 'test'})
        self.assertEqual((result.status_code, result.json()['data']['status']), (200, 'LOCKED'))
        self.assertIsNone(result.json()['data']['locked_until'])
        self.assertEqual(self.request('GET', path, 1).json()['data']['status'], 'LOCKED')
        self.assertEqual(self.request('PATCH', path + '/unlock', 1, json={}).json()['data']['status'], 'ACTIVE')

if __name__ == '__main__': unittest.main()
