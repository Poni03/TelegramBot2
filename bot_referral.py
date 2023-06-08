
class Referr:

    def encrypt_referral_link(referral_link):
        encrypted_link = ""
        for char in str(referral_link):
            encrypted_char = chr((ord(char) + 17) % 128)
            encrypted_link += encrypted_char
        return encrypted_link


    def decrypt_referral_link(encrypted_link):
        decrypted_link = ""
        for char in str(encrypted_link):
            decrypted_char = chr((ord(char) - 17) % 128)
            decrypted_link += decrypted_char
        return decrypted_link

  