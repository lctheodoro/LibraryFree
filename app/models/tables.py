from app import app, db
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

# Relationship table for many-to-many relation between books and users
owned_books = db.Table("owned_books",
    db.Column('book_id', db.Integer, db.ForeignKey('books.id')),
    db.Column('owner_id', db.Integer, db.ForeignKey('users.id'))
)


class User(db.Model):
    __tablename__ = "users"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # ID fields
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    # Complementary info
    city = db.Column(db.String)
    phone = db.Column(db.String)
    # insert avatar field

    # If the user is the manager of a organization, this field is user_id
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))

    # The list of books an user have
    books = db.relationship('Book', secondary=owned_books, backref='owners')

    # The lists of loans the user is participating
    my_loans = db.relationship('Book_loan', foreign_keys='Book_loan.user_id')
    loaned = db.relationship('Book_loan', foreign_keys='Book_loan.owner_id')

    # User evaluation from feedback
    evaluation = db.Column(db.Integer, default=0)

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
            'email': self.email,
            'city': self.city,
            'phone': self.phone,
            'evaluation': self.evaluation,
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


class Book(db.Model):
    __tablename__ = "books"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Description fields
    title = db.Column(db.String, nullable=False)
    isbn = db.Column(db.Integer)
    synopsis = db.Column(db.Text)
    # insert image field
    author = db.Column(db.String, nullable=False)
    author2 = db.Column(db.String)
    author3 = db.Column(db.String)
    publisher = db.Column(db.String, nullable=False)
    edition = db.Column(db.Integer)
    year = db.Column(db.Integer)
    language = db.Column(db.String)
    genre = db.Column(db.String)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'isbn' : self.isbn,
            'synopsis': self.synopsis,
            'author': self.author,
            'author2': self.author2,
            'author3': self.author3,
            'publisher': self.publisher,
            'edition': self.edition,
            'year': self.year,
            'language': self.language,
            'genre': self.genre
        }

    def __repr__(self):
        return "<Book %r>" % self.title


class Book_loan(db.Model):
    __tablename__ = "book_loans"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Relationships
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    book = db.relationship('Book')
    owner = db.relationship('User', foreign_keys=owner_id)
    user = db.relationship('User', foreign_keys=user_id)

    # Transaction info
    loan_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=False)

    # Loan status:
    # requested - user requested the book
    # accepted - owner accepted user request
    # refused - owner refused user request
    # queue - user is in the queue
    loan_status = db.Column(db.Enum('requested', 'accepted',
                                    'refused', 'queue',
                                    name="loan_status"))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'book': self.book.serialize,
            'owner': self.owner.serialize,
            'user': self.user.serialize,
            'loan_date': self.loan_date.strftime('%Y-%m-%d'),
            'return_date': self.return_date.strftime('%Y-%m-%d'),
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
            'returned_date': self.returned_date,
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
                               name="delayed_return_status"))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'book_loan': self.book_loan.serialize,
            'requested_date': self.requested_date,
            'status': self.status
        }

    def __repr__(self):
        return "<Request of delayed return for %r>" % self.book_loan_id


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Feedback info
    transaction_id = db.Column(db.Integer, db.ForeignKey('book_loans.id'), nullable=False)
    user = db.Column(db.Enum("owner", "user", name="user_feedback"), nullable=False)
    user_evaluation = db.Column(db.Integer, nullable=False)
    time_evaluation = db.Column(db.Integer)
    book_evaluation = db.Column(db.Integer)
    interaction_evaluation = db.Column(db.Integer)
    comments = db.Column(db.Text)

    book_loan = db.relationship('Book_loan', foreign_keys=transaction_id)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'book_loan': self.book_loan.serialize,
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
    isbn = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String, nullable=False)
    user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'isbn': self.isbn,
            'title': self.title,
            'user': self.user
        }

    def __repr__(self):
        return "<Wishlist %r>" % self.title
