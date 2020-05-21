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
    return datetime.now().strftime('%d. %m. %Y.')


def get_most_recent_posts():
    q = '''
    match (u:User)-[po:POSTED]->(p:Post)<-[ha:HASHTAGGING]-(h:Hashtag)
    return u, p, collect(h.tag) as htags
    order by p.timestamp desc limit 10
    '''

    return graph.run(q)

def get_recent_posts():
    posts = graph.evaluate('''
    match (p:Post)
    return collect(p)
    limit 10
    ''')

    return posts


###### IDEJA ZA KOMENTARE: mozda ima i nesto bolje
## ili promijeniti smjer jednog od bridova

#match (u:User)-[po:POSTED]->(p:Post)<-[ha:HASHTAGGING]-(h:Hashtag)
#with u, p, h
#match (u2:User)-[w:WROTE]->(c:Comment)-[o:ON]->(p2:Post)
#where p.id = p2.id
#return u, p, collect(h.tag) as htags, c, u2
#order by p.timestamp limit 10


class User:
    def __init__(self, username):
        self.username = username
    
    def find(self):
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
    
    def change_password(self, new_password):
        q = '''
        match (u:User)
        where u.username = $uname
        set u.password = $password
        '''
        return graph.run(q, uname=self.username, password=bcrypt.encrypt(new_password))

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
    
    def get_my_posts(self):
        q = '''
        match (u:User)-[po:POSTED]->(p:Post)<-[ha:HASHTAGGING]-(h:Hashtag)
        where u.username = $uname
        return u, p, collect(h.tag) as htags
        order by p.timestamp desc
        '''

        return graph.run(q, uname=self.username)

    def get_my_image(self):
        im = graph.evaluate('''
        match (u:User)
        where u.username = $uname
        return u.image
        ''', uname=self.username
        ) 
        return im

    
    def add_comment(self, pid, text):
        post = Post(pid).find()
        user = self.find()
        body = text
        comment = Node(
            'Comment',
            id=str(uuid.uuid4()),
            body=body,
            timestamp=get_timestamp(),
            date=get_date()
        )
        relation_user_comment = Relationship(
            user,
            'WROTE',
            comment
        )
        graph.create(relation_user_comment)
        relation_comment_post = Relationship(
            comment,
            'ON',
            post
        )
        graph.create(relation_comment_post)


    def get_similar_users(self):
        q = '''
        match (i:User)-[:POSTED]->(:Post)<-[:HASHTAGGING]-(h:Hashtag),
        (similar:User)-[:POSTED]->(:Post)<-[:HASHTAGGING]-(h)
        where i.username = $uname and i.username <> similar.username
        return similar, collect(distinct h.tag) as htags
        order by size(htags) desc
        '''
        return graph.run(q, uname=self.username)
    

    def change_profile_picture(self, image_path):
        q = '''
        match (u:User) where u.username = $uname
        set u.image = $image
        '''
        return graph.run(q, uname=self.username, image=image_path)


class Hashtag:
    def __init__(self, tag):
        self.tag = tag
    
    def find(self):
        ht = graph.evaluate(
            '''
            match (h:Hashtag) 
            where h.tag=$htag
            return h limit 1 
            ''', htag=self.tag
        )
        return ht


class Post:   
    def __init__(self, post_id):
        self.id = post_id

    def find(self):
        p = graph.evaluate(
            '''
            match (p:Post) where p.id=$pid
            return p limit 1 
            ''', pid=self.id
        )  
        return p
    
    def get_details(self):
        q = '''
        match (u:User)-[po:POSTED]->(p:Post)<-[ha:HASHTAGGING]-(h:Hashtag)
        where p.id = $pid
        return u, p, collect(h.tag) as htags
        '''
        return graph.run(q, pid=self.id)
    
    def get_author(self):
        u = graph.evaluate(
            '''
            match (u:User)-[po:POSTED]->(p:Post) 
            where p.id=$pid
            return u limit 1 
            ''', pid=self.id
        )  
        return u
    
    def get_hashtags(self):
        h = graph.evaluate(
            '''
            match (h:Hashtag)-[ha:HASHTAGGING]->(p:Post) 
            where p.id=$pid
            return collect(h.tag) as htags 
            ''', pid=self.id
        )
        return h
        
    
    def get_comments(self):
        q= '''
        match (u:User)-[w:WROTE]->(c:Comment)-[o:ON]->(p:Post) 
        where p.id=$pid
        return u, c
        order by c.timestamp  
        '''
        return graph.run(q, pid=self.id)



