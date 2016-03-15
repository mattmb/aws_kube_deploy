import time
def timeout(timeout, interval):
    def decorate(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while True:
                result = func(*args, **kwargs)
                if result:
                    return result
                if attempts >= timeout / interval:
                    raise Exception("Timeout in: {0}".format(func.__name__))
                attempts += 1
                time.sleep(interval)
        return wrapper
    return decorate
