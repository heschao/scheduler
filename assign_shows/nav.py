NAV_ITEMS = {
    "home": "index",
    "shows": "add_show",
    "students": "add_student",
    "assignments": "assignments"
}


class NavItem(object):
    """
        <li class={{ item.li_class }}>
        <a class={{ item.a_class }} href={{ url_for(item.url) }}>{{ item.text }}</a>
    </li>
    """

    def __init__(self, url, text, is_active=False):
        self.li_class = "nav-item" + " active" if is_active else ""
        self.a_class = "nav-link"
        self.url = url
        self.text = text