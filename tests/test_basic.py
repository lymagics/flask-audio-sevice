import unittest

from flask import current_app

from app import create_app, db


class BasicTestCase(unittest.TestCase):
    """Basic case to test application."""
    
    def setUp(self):
        """Test case setup."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        """Test case tear down."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_app_exist(self):
        """Check is application exist.
        
        """
        self.assertTrue(current_app is not None)
    
    def test_app_is_testing(self):
        """Test is application in testing mode.
        
        """
        self.assertTrue(current_app.config["TESTING"])
        