from app import db

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

    # The list of loans the user is participating
    loans = db.relationship('Book_loan', lazy='dynamic')

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
    managers = db.relationship('User', backref='organization', lazy='dynamic')

    def __repr__(self):
        return "<Organization %r>" % self.name


class Book(db.Model):
    __tablename__ = "books"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Description fields
    title = db.Column(db.String, nullable=False)
    synopsis = db.Column(db.Text)
    # insert image field
    author = db.Column(db.String, nullable=False)
    publisher = db.Column(db.String, nullable=False)
    edition = db.Column(db.Integer)
    year = db.Column(db.Integer)
    language = db.Column(db.String)
    genre = db.Column(db.String)

    def __repr__(self):
        return "<Book %r>" % self.title


class Book_loan(db.Model):
    __tablename__ = "book_loans"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Transaction info
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
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

    def __repr__(self):
        return "<Book %r to user %r>" % (self.book_id, self.user_id)


class Book_return(db.Model):
    __tablename__ = "book_returns"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Return info
    book_loan_id = db.Column(db.Integer, db.ForeignKey('book_loans.id'))
    returned_date = db.Column(db.Date, nullable=False)
    user_confirmation = db.Column(db.Boolean)
    owner_confirmation = db.Column(db.Boolean)

    def __repr__(self):
        return "<End of book loan %r>" % self.book_loan_id


class Delayed_return(db.Model):
    __tablename__ = "delayed_returns"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Delayed return info
    book_loan_id = db.Column(db.Integer, db.ForeignKey('book_loans.id'))
    requested_date = db.Column(db.Date, nullable=False)

    # Request status:
    # waiting - waiting owner reply
    # accepted - owner accepted to delay the return date
    # refused - owner refused to delay the return date
    status = db.Column(db.Enum("waiting", "accepted", "refused",
                               name="delayed_return_status"))

    def __repr__(self):
        return "<Request of delayed return for %r>" % self.book_loan_id


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Feedback info
    transaction_id = db.Column(db.Integer, db.ForeignKey('book_loans.id'))
    user = db.Column(db.Enum("owner", "user", name="user_feedback"))
    user_evaluation = db.Column(db.Integer)
    time_evaluation = db.Column(db.Integer)
    book_evaluation = db.Column(db.Integer)
    comments = db.Column(db.Text)

    def __repr__(self):
        return "<Feedback %r>" % self.id
