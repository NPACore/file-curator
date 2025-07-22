try:
    import tomllib as toml
except ModuleNotFoundError:
    import toml  # For Python < 3.11

def read_emails(toml_path):
    """
    Load the TOML email config and return a list of email recipient entries.

    >>> emails = read_emails('shim-emails.toml')
    >>> len(emails) > 0
    True
    >>> [e["to"] for e in emails]
    ['foranw@umpc.edu', 'hudlowe@upmc.edu', 'hudlowe@pitt.edu', 'flywheelgearlist@list.pitt.edu']
    >>> "host" in emails[0]
    True
    """
    with open(toml_path, "rb") as fh:
        config = toml.load(fh)
    recips = config["recipients"]
    return [
        {
            "host": recips["host"],
            "from": recips["from"],
            "to": to
        }
        for to in recips["to"]
    ]

