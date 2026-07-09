def save_profile(backend, user, response, *args, **kwargs):
    """Salva first_name e last_name do Google/Facebook"""
    if backend.name == 'google-oauth2':
        user.first_name = response.get('given_name', '')
        user.last_name = response.get('family_name', '')
        user.save()
    
    elif backend.name == 'facebook':
        name = response.get('name', '')
        name_parts = name.split(' ', 1)
        user.first_name = name_parts[0] if name_parts else ''
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        user.save()


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    """Cria usuário com first_name e last_name"""
    if user:
        return {'is_new': False}
    
    fields = {
        'email': details.get('email'),
        'username': details.get('username') or details.get('email').split('@')[0],
        'first_name': details.get('first_name') or 'Usuário',
        'last_name': details.get('last_name') or 'Google',
    }
    
    user = strategy.create_user(**fields)
    return {
        'is_new': True,
        'user': user
    }