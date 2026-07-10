"""Root conftest — its mere presence makes pytest insert this directory onto
`sys.path`, so `import src...` works whether tests are run as `pytest`,
`python -m pytest`, or from a different working directory.
"""
