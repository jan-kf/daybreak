import time

def debounce(wait):
    def decorator(fn):
        last_call_time = 0
        
        def debounced(*args, **kwargs):
            nonlocal last_call_time
            current_time = time.time()
            
            if current_time - last_call_time >= wait:
                result = fn(*args, **kwargs)
                last_call_time = current_time
                return result
                
        return debounced
        
    return decorator