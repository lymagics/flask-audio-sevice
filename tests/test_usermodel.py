import unittest
from time import sleep

from app import create_app, db
from app.models import AnonymousUser, User, Role, Permission


class UserModelTestCase(unittest.TestCase):
    """Case to test user model."""
    def setUp(self):
        """Test case set up."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
    
    def tearDown(self):
        """Test case tear down."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_generate_hash_is_correct(self):
        """Test hash generation is correct."""
        u = User(username="john", password="cat")
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.verify_password("cat"))
        self.assertFalse(u.verify_password("dog"))
        
    def test_hash_salts_are_random(self):
        """Test hash salts are random to generate different hashes."""
        u1 = User(username="john", password="cat")
        u2 = User(username="alex", password="cat")
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertTrue(u1.password_hash != u2.password_hash)
        
    def test_password_getter_raises_error(self):
        """Test password getter raises Attribute error when user tries get it."""
        u = User(username="john", password="cat")
        with self.assertRaises(AttributeError):
            u.password  
    
    def test_confirmation_token(self):
        """Test confirmation token is valid."""
        u = User(username="john", password="cat")
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.validate_confirmation_token(token))
        db.session.commit()
        self.assertTrue(u.confirmed)
        
    def test_confirmation_token_expires(self):
        """Test confirmation token expires."""
        u = User(username="john", password="cat")
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(expiration=2)
        sleep(3)
        self.assertFalse(u.validate_confirmation_token(token))
        self.assertFalse(u.confirmed)
    
    def test_confirmation_token_invalid_for_another_user(self):
        """Test confirmation token invalid for another user."""
        u1 = User(username="john", password="cat")
        u2 = User(username="alex", password="cat")
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.validate_confirmation_token(token))
        self.assertFalse(u1.confirmed)
        self.assertFalse(u2.confirmed)
    
    def test_user_role(self):
        """Test user role permissions."""
        u = User(username="john", password="cat")
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.PUBLISH))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))
    
    def test_moderation_role(self):
        """Test moderator role permissions."""
        u = User(username="john", password="cat")
        u.role = Role.query.filter_by(name="Moderator").first()
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.PUBLISH))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))
    
    def test_administrator_role(self):
        """Test administrator role permissions."""
        u = User(username="john", password="cat")
        u.role = Role.query.filter_by(name="Administrator").first()
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.PUBLISH))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertTrue(u.can(Permission.ADMIN))
    
    def test_anonymous_user_role(self):
        """Test anonymous user role permissions."""
        a = AnonymousUser()
        self.assertFalse(a.can(Permission.FOLLOW))
        self.assertFalse(a.can(Permission.PUBLISH))
        self.assertFalse(a.can(Permission.COMMENT))
        self.assertFalse(a.can(Permission.MODERATE))
        self.assertFalse(a.can(Permission.ADMIN))
    