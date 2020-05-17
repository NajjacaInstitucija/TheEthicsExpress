from py2neo import Graph, Node, Relationship, NodeMatcher
from datetime import datetime
from passlib.hash import bcrypt
import os
import uuid


#url = os.environ.get('blogproba', 'http://localhost:7474')
#username = os.environ.get('NEO4J_USERNAME')
#password = os.environ.get('NEO4J_PASSWORD')

#graph = Graph(url + '/db/data', username=username, password=password)
graph = Graph()
#matcher = NodeMatcher(graph)

class User:
    def __init__(self, username):
        self.username = username
    
    def find(self):
        #user = graph.nodes.match('User', username=self.username).first()
        user = graph.evaluate(
            '''
            match (u:User) where u.username=$usname
            return u limit 1 
            ''', usname=self.username
        )
        print("alalala")
        return user
    
    def register(self, password):
        if not self.find():
            user = Node('User', username=self.username, password=bcrypt.encrypt(password))
            graph.create(user)
            return True
        else:
            return False
    
    def verify(self, password):
        if not self.find():
            return False
        else:
            user = self.find()
            return bcrypt.verify(password, user['password'])
        





