from app import db, User

users = User.query.all()
for user in users:
    if user.profile_image and user.profile_image.startswith('uploads/uploads/'):
        user.profile_image = user.profile_image.replace('uploads/uploads/', 'uploads/')
        db.session.commit()