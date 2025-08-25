# User Management Features

This document describes the enhanced user management functionality added to the RMS Booking Chart Defragmenter.

## New Features

### 1. User Profile Management

- **Email Address**: All users now require an email address for future 2FA implementation
- **Profile Editing**: Users can edit their first name, last name, and email address
- **Profile Updates**: Changes are tracked with timestamps

### 2. Password Management

- **Strong Password Requirements**:
  - Minimum 12 characters
  - Must contain uppercase and lowercase letters
  - Must contain at least one digit
  - Must contain at least one special character
  - Cannot contain common weak patterns (123, abc, qwe, password, admin, user)
  - Cannot contain keyboard patterns (qwerty, asdfgh, etc.)
  - Cannot contain 3+ consecutive identical characters
- **Password Changes**: Users can change their password with current password verification
- **Admin Password Reset**: Admins can reset passwords for other users

### 3. Admin User Management

- **User Creation**: Admins can create new users with full profile information
- **User Listing**: Admins can view all users in the system
- **User Updates**: Admins can modify user profiles and status
- **User Deletion**: Admins can delete non-admin users
- **Admin Protection**: Admin users cannot be deleted or have admin privileges removed

### 4. Enhanced Security

- **Account Status**: Users can be marked as active/inactive
- **Login Tracking**: Last login time is recorded
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access**: Different permissions for regular users vs. admins

## API Endpoints

### Authentication

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user info
- `PUT /api/v1/auth/me` - Update current user profile
- `PUT /api/v1/auth/me/change-password` - Change current user password

### Admin Only

- `GET /api/v1/auth/users` - List all users
- `POST /api/v1/auth/users` - Create new user
- `PUT /api/v1/auth/users/{user_id}` - Update user
- `DELETE /api/v1/auth/users/{user_id}` - Delete user
- `PUT /api/v1/auth/users/{user_id}/reset-password` - Reset user password

## Database Schema Changes

### Users Table

- Added `email` field (required, unique)
- Added `first_name` and `last_name` fields
- Added `is_active` field for account status
- Added `last_login` field for tracking
- Added `updated_at` field for change tracking

### Indexes

- Email index for fast lookups
- Active status index for filtering

## Password Validation Rules

The system enforces strong passwords using the following criteria:

1. **Length**: Minimum 12 characters
2. **Character Types**:
   - At least one uppercase letter (A-Z)
   - At least one lowercase letter (a-z)
   - At least one digit (0-9)
   - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
3. **Pattern Restrictions**:
   - No consecutive identical characters (e.g., "aaa")
   - No common weak words (password, admin, user, 123, abc, qwe)
   - No keyboard patterns (qwerty, asdfgh, zxcvbn)
4. **Strength Scoring**: System calculates password strength (0-100)

## Frontend Features

### User Interface

- **Profile Dropdown**: Access to profile editing, password changes, and user management
- **Modal Forms**: Clean, user-friendly forms for all operations
- **Real-time Validation**: Immediate feedback on password strength
- **Admin Controls**: Special interface elements for admin users

### User Management Dashboard

- **User List**: View all users with key information
- **User Actions**: Edit, delete, and manage user accounts
- **Status Indicators**: Visual indicators for user status and admin privileges
- **Create User Form**: Comprehensive form for adding new users

## Migration

The system includes an automatic migration script (`migrate_admin_user.py`) that:

1. Adds new columns to the existing users table
2. Updates the admin user with email and profile information
3. Creates necessary database indexes
4. Ensures data integrity during the upgrade

## Testing

A comprehensive test script (`test_user_management.py`) is provided to verify:

- User authentication and authorization
- Profile management functionality
- Password validation and changes
- Admin user management features
- Security restrictions and protections

## Security Considerations

1. **Password Hashing**: All passwords are hashed using bcrypt
2. **JWT Tokens**: Secure, time-limited authentication tokens
3. **Input Validation**: Comprehensive validation of all user inputs
4. **Access Control**: Role-based permissions for sensitive operations
5. **Audit Trail**: Tracking of user actions and changes

## Future Enhancements

1. **Two-Factor Authentication**: Email-based 2FA using stored email addresses
2. **Password Expiration**: Automatic password change requirements
3. **Login History**: Detailed tracking of login attempts and locations
4. **User Groups**: Role-based access control with custom permissions
5. **Audit Logging**: Comprehensive logging of all administrative actions

## Usage Examples

### Creating a New User (Admin)

```bash
curl -X POST "http://localhost:8000/api/v1/auth/users" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "StrongPass123!@#",
    "first_name": "New",
    "last_name": "User",
    "is_admin": false
  }'
```

### Changing Password

```bash
curl -X PUT "http://localhost:8000/api/v1/auth/me/change-password" \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "oldpassword",
    "new_password": "NewStrongPass456!@#"
  }'
```

### Updating Profile

```bash
curl -X PUT "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com",
    "first_name": "Updated",
    "last_name": "Name"
  }'
```

## Deployment

The enhanced system can be deployed using the updated deployment script:

```bash
./deploy_web_app.sh
```

This will automatically:

1. Deploy the updated application
2. Run database migrations
3. Update the admin user with new fields
4. Enable all new user management features
