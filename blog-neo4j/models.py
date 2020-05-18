from py2neo import Graph, Node, Relationship, NodeMatcher
from datetime import datetime
from passlib.hash import bcrypt
import os
import uuid


#url = os.environ.get('blogproba', 'http://localhost:7474')
#username = os.environ.get('NEO4J_USERNAME')
#password = os.environ.get('NEO4J_PASSWORD')

#graph = Graph(url + '/db/data', username=username, password=password)

#premade constraints:
#create constraint on (u:User) assert u.username is unique
#create constraint on (p:Post) assert p.id is unique
#create constraint on (h:Hashtag) assert h.tag is unique
#create constraint on (c:Comment) assert c.id is unique
graph = Graph()


def get_timestamp():
    past = datetime.utcfromtimestamp(0)
    diff = datetime.now() - past
    return diff.total_seconds()


def get_date():
    return datetime.now().strftime('%Y-%m-%d')

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
    
    def new_post(self, header, hashtags, body):
        post = Node(
            'Post',
            id=str(uuid.uuid4()),
            header = header,
            body = body,
            timestamp = get_timestamp(),
            date = get_date()
        )
        user = self.find()
        relation = Relationship(
            user,
            'POSTED',
            post
        )
        graph.create(relation)
        htags = [htag.strip('#') for htag in hashtags.split(', ')]
        for ht in set(htags):
            if len(ht) > 0:
                if not Hashtag(ht).find():
                    ht_node = Node('Hashtag', tag=ht)
                   
                else: 
                    ht_node = Hashtag(ht).find()
                
                graph.create(ht_node)
                relation = Relationship(
                    ht_node,
                    'HASHTAGGING',
                    post
                    )
                graph.create(relation)


class Hashtag:
    def __init__(self, tag):
        self.tag = tag
    
    def find(self):
        ht = graph.evaluate(
            '''
            match (h:Hashtag) where h.tag=$htag
            return h limit 1 
            ''', htag=self.tag
        )
        return ht

        




