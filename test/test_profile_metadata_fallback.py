"""Unit tests for profile metadata query and fallback handling."""

import sys
import unittest

import pip._vendor.requests as requests
import pip._vendor.urllib3 as urllib3

sys.modules.setdefault("requests", requests)
sys.modules.setdefault("urllib3", urllib3)

from instaloader import Profile  # pylint:disable=wrong-import-position


class FakeContext:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []
        self.errors = []

    def doc_id_graphql_query(self, doc_id, variables):
        self.calls.append((doc_id, variables))
        response = self.responses.get(doc_id)
        if isinstance(response, Exception):
            raise response
        return response

    def get_json(self, path, params):
        if path == "web/search/topsearch/":
            query = params["query"]
            return {"users": [{"user": {"username": query, "id": "1"}}]}
        raise AssertionError("Unexpected get_json call: {}".format(path))

    def error(self, msg, repeat_at_end=True):
        self.errors.append((msg, repeat_at_end))


class TestProfileMetadataFallback(unittest.TestCase):
    def test_uses_current_profile_page_doc_id_and_payload(self):
        context = FakeContext({
            "27937681195819736": {
                "data": {
                    "user": {
                        "id": "1",
                        "username": "sook_0",
                        "media_count": 12,
                        "follower_count": 34,
                        "following_count": 56,
                        "is_private": False,
                    }
                }
            }
        })
        profile = Profile(context, {"id": "1", "username": "sook_0"})

        profile._obtain_metadata()  # pylint:disable=protected-access

        self.assertEqual("27937681195819736", context.calls[0][0])
        self.assertEqual({
            "id": "1",
            "enable_integrity_filters": True,
            "__relay_internal__pv__PolarisCannesGuardianExperienceEnabledrelayprovider": True,
            "__relay_internal__pv__PolarisCASB976ProfileEnabledrelayprovider": False,
            "__relay_internal__pv__PolarisWebSchoolsEnabledrelayprovider": False,
            "__relay_internal__pv__PolarisRepostsConsumptionEnabledrelayprovider": False,
        }, context.calls[0][1])
        self.assertTrue(profile._has_full_metadata)  # pylint:disable=protected-access

if __name__ == "__main__":
    unittest.main()
