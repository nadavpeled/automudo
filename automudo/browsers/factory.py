from .chrome import ChromeBrowser

SUPPORTED_BROWSERS = [ChromeBrowser]


def create_browser(browser_name, **kwargs):
    """
        Finds the class that inherits Browser
        and has the given browser name,
        and initializes an object of it using kwargs.
    """
    for browser in SUPPORTED_BROWSERS:
        if browser.name == browser_name:
            return browser(**kwargs)
    return KeyError("Browser {} not found. Supported browsers are: {}".format(
        browser_name,
        ", ".join(browser.name for browser in SUPPORTED_BROWSERS)
        ))
