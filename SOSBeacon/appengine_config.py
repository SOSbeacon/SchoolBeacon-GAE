
import webapp2
from webapp2_extras import sessions

def namespace_manager_default_namespace_for_request():
    try:
        session_store = sessions.get_store()
        session = session_store.get_session()
    except:
        # This means we're hitting a url w/o config.  Silo the user.
        return _get_user_namespace()

    if session:
        namespace = session.get('n')
        if namespace:
            # Distinguish company from individual namespaces.
            return '_' + str(namespace)

    return _get_user_namespace()

def _get_user_namespace():
    from google.appengine.api import users
    user = users.get_current_user()
    return user.user_id() if user else '_x_'

