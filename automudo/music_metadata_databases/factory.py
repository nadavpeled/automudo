from .discogs import DiscogsMetadataDatabase

SUPPORTED_DATABASES = [DiscogsMetadataDatabase]


def create_music_metadata_database(database_name, **kwargs):
    """
        Finds the class that inherits Database
        and has the given database name,
        and initializes an object of it using kwargs.
    """
    for database in SUPPORTED_DATABASES:
        if database.name == database_name:
            return database(**kwargs)
    return KeyError(
        "Database {} not found. Supported databases are: {}".format(
            database_name,
            ", ".join(database.name for database in SUPPORTED_DATABASES)
            ))
