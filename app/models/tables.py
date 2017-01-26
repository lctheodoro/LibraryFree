from app import app, db
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

class User(db.Model):
    __tablename__ = "users"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # ID fields
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    admin = db.Column(db.Integer, default=0)

    # Complementary info
    city = db.Column(db.String)
    phone = db.Column(db.String)
    # insert avatar field

    # If the user is the manager of a organization, this field is user_id
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))

    # The list of books an user have
    # books = db.relationship('Book', secondary=owned_books, backref='owners')

    # The lists of loans the user is participating
    my_loans = db.relationship('Book_loan', foreign_keys='Book_loan.user_id')

    # User evaluation from feedback
    evaluation = db.Column(db.Integer, default=0)

    # User points
    points = db.Column(db.Integer, default=0)
    complete = db.Column(db.Boolean, default=False)

    # User medals
    medals = db.Column(db.Enum('Usuario Iniciante','Usuario Bronze','Usuario Prata',
                                'Usuario Ouro','Usuario Diamante', name="users_medals"),
                                    nullable=False,default='Usuario Iniciante')

    # Check if user's registration is complete
    def check_register(self):
        if self.city != None and self.phone != None:
            if self.complete is False:
                self.complete = True
                self.points += 5
        else:
            if self.complete == True:
                self.points -= 5
            self.complete = False

    # Update points and medals
    def points_update(self,points):
        self.points += points
        self.check_register();
        if self.points >= 0 and self.points <= 19:
            self.medals = 'Usuario Iniciante'
        elif self.points >= 20 and self.points <= 49:
            self.medals = 'Usuario Bronze'
        elif self.points >=50 and self.points <= 89:
            self.medals = 'Usuario Prata'
        elif self.points >= 90 and self.points <= 139:
            self.medals = 'Usuario Ouro'
        elif self.points >= 140:
            self.medals = 'Usuario Diamante'

    # encrypts user's new password
    def hash_password(self, password):
        self.password = pwd_context.encrypt(password)

    # verifies if the password is correct
    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

    # generate an auth token so the user doesn't need to pass credentials
    def generate_auth_token(self, expiration=3600):
        # the token has an expiration time set to 3600
        # if the user logged time exceeds the expiration, the user have to
        # generate another token
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        # check if the token is valid and returns user info if it is
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user

    @property
    def serialize(self):
        if self.organization:
            org = self.organization.id
        else:
            org = None
        return {
            'id': self.id,
            'name': self.name,
            'admin': self.admin,
            'email': self.email,
            'city': self.city,
            'phone': self.phone,
            'evaluation': self.evaluation,
            'points': self.points,
            'medal': self.medals,
            'organization_id': org
        }

    def __repr__(self):
        return "<User %r>" % self.name


class Organization(db.Model):
    __tablename__ = "organizations"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Description fields
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.Text)
    # insert image field

    # The organization managers are available in this field
    managers = db.relationship('User', backref='organization')

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'managers': [m.serialize for m in self.managers]
        }

    def __repr__(self):
        return "<Organization %r>" % self.name


author_relationship = db.Table('author_relationship',
                                db.Column('book_id',db.Integer,db.ForeignKey('books.id'),nullable=False),
                                db.Column('author_id',db.Integer,db.ForeignKey('authors.id'),nullable=False),
                                db.PrimaryKeyConstraint('book_id','author_id'))

category_relationship = db.Table('category_relationship',
                                db.Column('book_id',db.Integer,db.ForeignKey('books.id'),nullable=False),
                                db.Column('category_id',db.Integer,db.ForeignKey('categories.id'),nullable=False),
                                db.PrimaryKeyConstraint('book_id','category_id'))
class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True,unique=True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }
    def __repr__(self):
        return "<Author %r>" % self.name

class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True,unique=True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }
    def __repr__(self):
        return "<Category %r>" % self.name

class Book(db.Model):
    __tablename__ = "books"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Description fields
    title = db.Column(db.String, nullable=False)
    subtitle = db.Column(db.String)

    isbn10 = db.Column(db.String)
    isbn13 = db.Column(db.String)

    avatarBase64 = db.Column(db.String)
    avatarUrl = db.Column(db.String)

    synopsis = db.Column(db.Text)
    publisher = db.Column(db.String)
    publisherDate = db.Column(db.String)
    description = db.Column(db.String)

    authors = db.relationship('Author',secondary=author_relationship, backref='books')
    categories = db.relationship('Category',secondary=category_relationship, backref='books')

    edition = db.Column(db.Integer)
    year = db.Column(db.Integer)
    language = db.Column(db.String)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    is_organization = db.Column(db.Boolean, default=False)
    available = db.Column(db.Boolean,default=True)

    user = db.relationship('User', foreign_keys=user_id)
    organization = db.relationship('Organization', foreign_keys=organization_id)


    @property
    def serialize(self):
        return {
            'id': self.id,
            'user_id' : self.user_id,
            'organization_id' : self.organization_id,
            'is_organization' : self.is_organization,
            'title': self.title,
            'subtitle': self.subtitle,
            'isbn10' : self.isbn10,
            'isbn13' : self.isbn13,
            'avatarBase64': self.avatarBase64,
            'avatarUrl': self.avatarUrl,
            'synopsis': self.synopsis,
            'publisher': self.publisher,
            'publisherDate': self.publisherDate,
            'description': self.description,
            'author': [a.serialize for a in self.authors],
            'categories': [c.serialize for c in self.categories],
            'publisher': self.publisher,
            'edition': self.edition,
            'year': self.year,
            'language': self.language,
        }

    def __repr__(self):
        return "<Book %r>" % self.title

class Book_loan(db.Model):
    __tablename__ = "book_loans"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Relationships
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    book = db.relationship('Book', foreign_keys=book_id)
    user = db.relationship('User', foreign_keys=user_id)

    # Transaction info
    loan_date = db.Column(db.Date)
    return_date = db.Column(db.Date)

    # Loan status:
    # requested - user requested the book
    # accepted - owner accepted user request
    # refused - owner refused user request
    # queue - user is in the queue
    # done - loan finished
    loan_status = db.Column(db.Enum('requested', 'accepted',
                                    'refused', 'queue','done',
                                    name="loan_status"))

    # Gamefication Info
    scored = db.Column(db.Boolean, default=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'loan_date': self.loan_date.strftime('%Y-%m-%d'),
            'return_date': self.return_date.strftime('%Y-%m-%d'),
            'loan_status': self.loan_status
        } if self.loan_status == 'accepted' else {
            'id': self.id,
            'loan_status': self.loan_status
        }


    def __repr__(self):
        return "<Book %r to user %r>" % (self.book_id, self.user_id)


class Book_return(db.Model):
    __tablename__ = "book_returns"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Return info
    book_loan_id = db.Column(db.Integer, db.ForeignKey('book_loans.id'))
    returned_date = db.Column(db.Date, nullable=False)
    user_confirmation = db.Column(db.Boolean, default=False)
    owner_confirmation = db.Column(db.Boolean, default=False)

    book_loan = db.relationship('Book_loan', foreign_keys=book_loan_id)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'book_loan': self.book_loan.serialize,
            'returned_date': str(self.returned_date),
            'user_confirmation': self.user_confirmation,
            'owner_confirmation': self.owner_confirmation
        }

    def __repr__(self):
        return "<End of book loan %r>" % self.book_loan_id


class Delayed_return(db.Model):
    __tablename__ = "delayed_returns"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Delayed return info
    book_loan_id = db.Column(db.Integer, db.ForeignKey('book_loans.id'))
    requested_date = db.Column(db.Date, nullable=False)

    book_loan = db.relationship('Book_loan', foreign_keys=book_loan_id)

    # Request status:
    # waiting - waiting owner reply
    # accepted - owner accepted to delay the return date
    # refused - owner refused to delay the return date
    status = db.Column(db.Enum("waiting", "accepted", "refused",
                               name="delayed_return_status"),default="waiting")

    @property
    def serialize(self):
        return {
            'id': self.id,
            'requested_date': str(self.requested_date),
            'status': self.status
        }

    def __repr__(self):
        return "<Request of delayed return for %r>" % self.book_loan_id


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Feedback info
    transaction_id = db.Column(db.Integer, db.ForeignKey('book_returns.id'), nullable=False)
    user = db.Column(db.Enum("owner", "user", name="user_feedback"))
    user_evaluation = db.Column(db.Integer, nullable=False)
    time_evaluation = db.Column(db.Integer)
    book_evaluation = db.Column(db.Integer)
    interaction_evaluation = db.Column(db.Integer)
    comments = db.Column(db.Text)
    scored = db.Column(db.Integer, default=0)

    book_return = db.relationship('Book_return', foreign_keys=transaction_id)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'book_return': self.book_return.serialize,
            'user_type': self.user,
            'user_evaluation': self.user_evaluation,
            'time_evaluation': self.time_evaluation,
            'book_evaluation': self.book_evaluation,
            'interaction_evaluation' : self.interaction_evaluation,
            'comments': self.comments
        }

    def __repr__(self):
        return "<Feedback %r>" % self.id


class Wishlist(db.Model):
    __tablename__ = "wishlists"

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)

    user = db.relationship('User', foreign_keys=user_id)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'isbn': self.isbn,
            'title': self.title,
            'user': self.user.serialize
        }

    def __repr__(self):
        return "<Wishlist %r>" % self.isbn

class Topsearches(db.Model):
    __tablename__ = "topsearches"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    isbn10 = db.Column(db.String, nullable=False)
    isbn13 = db.Column(db.String, nullable=False)
    times = db.Column(db.Integer, default=0)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'isbn10': self.isbn10,
            'isbn13': self.isbn13,
            'title': self.title,
            'times': self.times
        }

    def __repr__(self):
        return "<Topsearches %r>" % self.id
