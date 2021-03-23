import os


def flush(dsn, only_tokens=True, only_requests=True):
    os.environ[
        'DSN'] = dsn

    args = ''
    if only_tokens:
        args += ' --tokens'
    if only_requests:
        args += ' --requests'

    return os.system(f'.build/hydra/hydra janitor {args} -e')
