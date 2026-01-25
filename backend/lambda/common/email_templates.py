"""
Email templates for group invitations
"""


def get_existing_user_email(inviter_name, group_name, group_description, invite_url):
    """
    Email template for users who already have an account

    Args:
        inviter_name: Name of the person sending the invitation
        group_name: Name of the group
        group_description: Description of the group (can be None)
        invite_url: Full invitation URL

    Returns:
        tuple: (subject, html_body, text_body)
    """
    subject = f"{inviter_name} invited you to join {group_name} on Presently"

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ padding: 30px 20px; background: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #2563eb;
                  color: white; text-decoration: none; border-radius: 6px; margin: 20px 0;
                  font-weight: 600; }}
        .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        .link-text {{ word-break: break-all; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">🎁 Presently</h1>
        </div>
        <div class="content">
            <h2>You've been invited to join a group!</h2>
            <p>Hi there,</p>
            <p><strong>{inviter_name}</strong> has invited you to join the group
               <strong>"{group_name}"</strong> on Presently.</p>
            {f'<p style="color: #666; font-style: italic;">{group_description}</p>' if group_description else ''}
            <p>Click the button below to join this group:</p>
            <div style="text-align: center;">
                <a href="{invite_url}" class="button">Join Group</a>
            </div>
            <p style="color: #666; font-size: 14px; margin-top: 20px;">
                Or copy this link: <br/>
                <span class="link-text">{invite_url}</span>
            </p>
            <p style="margin-top: 30px;">
                Once you join, you'll be able to see everyone's wishlists and share your own!
            </p>
        </div>
        <div class="footer">
            <p>This invitation will expire in 7 days.</p>
            <p>© 2026 Presently - Wishlist sharing made simple</p>
        </div>
    </div>
</body>
</html>
    """

    text_body = f"""
You've been invited to join {group_name} on Presently!

{inviter_name} has invited you to join the group "{group_name}".
{f'Description: {group_description}' if group_description else ''}

Click here to join: {invite_url}

Once you join, you'll be able to see everyone's wishlists and share your own!

This invitation will expire in 7 days.

© 2026 Presently - Wishlist sharing made simple
    """

    return subject, html_body, text_body


def get_new_user_email(inviter_name, inviter_email, group_name, group_description, invite_url):
    """
    Email template for users who need to register first

    Args:
        inviter_name: Name of the person sending the invitation
        inviter_email: Email of the person sending the invitation
        group_name: Name of the group
        group_description: Description of the group (can be None)
        invite_url: Full invitation URL

    Returns:
        tuple: (subject, html_body, text_body)
    """
    subject = f"{inviter_name} invited you to join Presently"

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ padding: 30px 20px; background: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #2563eb;
                  color: white; text-decoration: none; border-radius: 6px; margin: 20px 0;
                  font-weight: 600; }}
        .info-box {{ background: #e0e7ff; border-left: 4px solid #2563eb;
                     padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        .link-text {{ word-break: break-all; font-size: 12px; color: #666; }}
        ul {{ line-height: 1.8; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">🎁 Presently</h1>
            <p style="margin: 10px 0 0 0; font-size: 14px;">Wishlist sharing made simple</p>
        </div>
        <div class="content">
            <h2>You've been invited to join Presently!</h2>
            <p>Hi there,</p>
            <p><strong>{inviter_name}</strong> ({inviter_email}) has invited you to join
               the group <strong>"{group_name}"</strong> on Presently.</p>
            {f'<p style="color: #666; font-style: italic;">{group_description}</p>' if group_description else ''}

            <div class="info-box">
                <h3 style="margin-top: 0;">What is Presently?</h3>
                <p style="margin-bottom: 0;">
                    Presently is a wishlist app that makes gift-giving easier and more thoughtful.
                    Create wishlists for yourself, see what your friends and family want,
                    and secretly claim items to purchase - all without spoiling the surprise!
                </p>
            </div>

            <p>Click the button below to create your account and join the group:</p>
            <div style="text-align: center;">
                <a href="{invite_url}" class="button">Sign Up & Join Group</a>
            </div>
            <p style="color: #666; font-size: 14px; margin-top: 20px;">
                Or copy this link: <br/>
                <span class="link-text">{invite_url}</span>
            </p>

            <p style="margin-top: 30px;">
                <strong>What you can do on Presently:</strong>
            </p>
            <ul>
                <li>Create and share wishlists with your groups</li>
                <li>See what others want (making gift-giving easy!)</li>
                <li>Secretly mark items as purchased</li>
                <li>Join multiple groups for different occasions</li>
            </ul>
        </div>
        <div class="footer">
            <p>This invitation will expire in 7 days.</p>
            <p>© 2026 Presently - Wishlist sharing made simple</p>
        </div>
    </div>
</body>
</html>
    """

    text_body = f"""
You've been invited to join Presently!

{inviter_name} ({inviter_email}) has invited you to join the group "{group_name}" on Presently.
{f'Description: {group_description}' if group_description else ''}

What is Presently?
Presently is a wishlist app that makes gift-giving easier and more thoughtful.
Create wishlists, see what your friends and family want, and secretly claim items
to purchase - all without spoiling the surprise!

Click here to sign up and join: {invite_url}

What you can do on Presently:
- Create and share wishlists with your groups
- See what others want (making gift-giving easy!)
- Secretly mark items as purchased
- Join multiple groups for different occasions

This invitation will expire in 7 days.

© 2026 Presently - Wishlist sharing made simple
    """

    return subject, html_body, text_body
