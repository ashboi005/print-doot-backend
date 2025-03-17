import string

def generate_order_id(counter: int):
    letters_part = counter // 99999 
    numbers_part = counter % 99999 + 1 
    
    # Generate letter code (AAA to ZZZ)
    def number_to_letters(n):
        letters = ""
        for _ in range(3):
            n, remainder = divmod(n, 26)
            letters = chr(65 + remainder) + letters
        return letters

    letters_code = number_to_letters(letters_part)
    order_id = f"PRNTDT-{letters_code}{str(numbers_part).zfill(5)}"
    return order_id
