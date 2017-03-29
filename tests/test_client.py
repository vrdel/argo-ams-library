import unittest
from httmock import urlmatch, HTTMock, response
from pymod import ArgoMessagingService
from pymod import AmsMessage
import json


class TestClient(unittest.TestCase):

    def setUp(self):
        # Initialize ams in localhost with token s3cr3t and project TEST
        self.ams = ArgoMessagingService(endpoint="localhost", token="s3cr3t", project="TEST")

    # Test create topic client request
    def testCreateTopics(self):
        # Mock response for PUT topic request
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/topics/topic1",
                  method="PUT")
        def create_topic_mock(url, request):
            assert url.path == "/v1/projects/TEST/topics/topic1"
            # Return two topics in json format
            return response(200, '{"name":"/v1/projects/TEST/topics/topic1"}', None, None, 5, request)
        # Execute ams client with mocked response
        with HTTMock(create_topic_mock):
            resp = self.ams.create_topic("topic1")
            # Assert that ams client handled the json response correctly
            name = resp["name"]
            assert name == "/v1/projects/TEST/topics/topic1"

    # Test Pull client request
    def testPull(self):
        # Mock response for GET subscription request
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/subscriptions/subscription1",
                  method="GET")
        def get_sub_mock(url, request):
            assert url.path == "/v1/projects/TEST/subscriptions/subscription1"
            # Return the details of a topic in json format
            return response(200, '{"name":"/v1/projects/TEST/subscriptions/subscription1"}', None, None, 5, request)

        # Mock response for POST pull from subscription
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/subscriptions/subscription1:pull",
                  method="POST")
        def pull_mock(url, request):
            assert url.path == "/v1/projects/TEST/subscriptions/subscription1:pull"


            # Check request produced by ams client
            req_body = json.loads(request.body)
            assert req_body["maxMessages"] == "1"
            return '{"receivedMessages":[{"ackId":"projects/TEST/subscriptions/subscription1:1221",\
                    "message":{"messageId":"1221","attributes":{"foo":"bar"},"data":"YmFzZTY0ZW5jb2RlZA==",\
                    "publishTime":"2016-02-24T11:55:09.786127994Z"}}]}'

        @urlmatch(netloc="localhost", path="/v1/projects/TEST/subscriptions/subscription1:acknowledge",
                  method="POST")
        def ack_mock(url, request):
            assert url.path == "/v1/projects/TEST/subscriptions/subscription1:acknowledge"
            # Error: library returns json in the form {"ackIds": 1221}
            assert request.body == '{"ackIds": ["1221"]}'
            # Check request produced by ams client
            return '{}'

        # Execute ams client with mocked response
        with HTTMock(pull_mock, ack_mock, get_sub_mock):

            # msg = AmsMessage(data='foo1', attributes={'bar1': 'baz1'}).dict()
            resp_pull = self.ams.pull_sub("subscription1", 1)
            ack_id, msg = resp_pull[0]
            assert ack_id == "projects/TEST/subscriptions/subscription1:1221"
            assert msg.data == "YmFzZTY0ZW5jb2RlZA=="
            assert msg.messageId == "1221"
            # Note: Maybe ack_sub should return a boolean
            resp_ack = self.ams.ack_sub("subscription1", ["1221"])
            assert resp_ack == {}

    def testCreateSubscription(self):
        # Mock response for GET topic request
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/topics/topic1",
                  method="GET")
        def get_topic_mock(url, request):

            assert url.path == "/v1/projects/TEST/topics/topic1"
            # Return the details of a topic in json format
            return response(200, '{"name":"/v1/projects/TEST/topics/topic1"}', None, None, 5, request)

        # Mock response for PUT topic request
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/subscriptions/subscription1",
                  method="PUT")
        def create_subscription_mock(url, request):
            assert url.path == "/v1/projects/TEST/subscriptions/subscription1"
            # Return two topics in json format
            return response(200,
                            '{"name": "/v1/projects/TEST/subscriptions/subscription1",\
                            "topic":"/v1/projects/TEST/topics/topic1",\
                            "pushConfig":{"pushEndpoint":"","retryPolicy":{}},"ackDeadlineSeconds": 10}',
                            None, None, 5, request)

        # Execute ams client with mocked response
        with HTTMock(create_subscription_mock, get_topic_mock):
            resp = self.ams.create_sub("subscription1", "topic1", 10)

            # Assert that ams client handled the json response correctly
            name = resp["name"]
            assert name == "/v1/projects/TEST/subscriptions/subscription1"

    # Test List topics client request
    def testListTopics(self):
        # Mock response for GET topics request
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/topics",
                  method="GET")
        def list_topics_mock(url, request):
            assert url.path == "/v1/projects/TEST/topics"
            # Return two topics in json format
            return response(200, '{"topics":[{"name":"/v1/projects/TEST/topic1"},\
                                  {"name":"/v1/projects/TEST/topic2"}]}', None, None, 5, request)

        # Execute ams client with mocked response
        with HTTMock(list_topics_mock):
            resp = self.ams.list_topics()
            # Assert that ams client handled the json response correctly
            topics = resp["topics"]
            assert len(topics) == 2
            assert topics[0]["name"] == "/v1/projects/TEST/topic1"
            assert topics[1]["name"] == "/v1/projects/TEST/topic2"

    # Test Get a topic client request
    def testGetTopic(self):
        # Mock response for GET topic request
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/topics/topic1",
                  method="GET")
        def get_topic_mock(url, request):
            assert url.path == "/v1/projects/TEST/topics/topic1"
            # Return the details of a topic in json format
            return response(200, '{"name":"/v1/projects/TEST/topics/topic1"}', None, None, 5, request)

        # Execute ams client with mocked response
        with HTTMock(get_topic_mock):
            resp = self.ams.get_topic("topic1")
            # Assert that ams client handled the json response correctly
            name = resp["name"]
            assert(name == "/v1/projects/TEST/topics/topic1")

    # Test Publish client request
    def testPublish(self):
        # Mock response for POST publish to topic
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/topics/topic1:publish",
                  method="POST")
        def publish_mock(url, request):
            assert url.path == "/v1/projects/TEST/topics/topic1:publish"
            # Check request produced by ams client
            req_body = json.loads(request.body)
            assert(req_body["messages"][0]["data"] == "Zm9vMQ==")
            assert (req_body["messages"][0]["attributes"]["bar1"] == "baz1")

            return '{"msgIds":["1"]}'

        # Execute ams client with mocked response
        with HTTMock(publish_mock):
            msg = AmsMessage(data='foo1', attributes={'bar1': 'baz1'}).dict()
            resp = self.ams.publish("topic1", msg)
            # Assert that ams client handled the json response correctly
            assert resp["msgIds"][0] == "1"

    # Test List Subscriptions client request

    # Test List Subscriptions client request
    def testListSubscriptions(self):
        # Mock response for GET Subscriptions request
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/subscriptions",
                  method="GET")
        def list_subs_mock(url, request):
            assert url.path == "/v1/projects/TEST/subscriptions"
            # Return two topics in json format
            return response(200, '{"subscriptions":[{"name": "/projects/TEST/subscriptions/subscription1",\
                                  "topic": "/projects/TEST/topics/topic1","pushConfig": \
                                  {"pushEndpoint": "","retryPolicy": {}},"ackDeadlineSeconds": 10},\
                                  {"name": "/projects/TEST/subscriptions/subscription2", \
                                  "topic": "/projects/TEST/topics/topic1", \
                                  "pushConfig": {"pushEndpoint": "","retryPolicy": {}},\
                                  "ackDeadlineSeconds": 10}]}', None, None, 5, request)

        # Execute ams client with mocked response
        with HTTMock(list_subs_mock):
            resp = self.ams.list_subs()
            subscriptions = resp["subscriptions"]
            # Assert that ams client handled the json response correctly
            assert len(subscriptions) == 2
            assert subscriptions[0]["name"] == "/projects/TEST/subscriptions/subscription1"
            assert subscriptions[1]["name"] == "/projects/TEST/subscriptions/subscription2"

    # Test Get a subscriptions client request
    def testGetSubscription(self):

        # Mock response for GET subscriptions request
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/subscriptions/subscription1",
                  method="GET")
        def get_sub_mock(url, request):
            assert url.path == "/v1/projects/TEST/subscriptions/subscription1"
            # Return the details of a subscription in json format
            return response(200, '{"name":"/v1/projects/TEST/subscriptions/subscription1"}', None, None, 5, request)

        # Execute ams client with mocked response
        with HTTMock(get_sub_mock):
            resp = self.ams.get_sub("subscription1")
            # Assert that ams client handled the json response correctly
            name = resp["name"]
            assert name == "/v1/projects/TEST/subscriptions/subscription1"

    # Test has topic client
    def testHasTopic(self):
        # Mock response for GET topic request
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/topics/topic1", method="GET")
        def has_topic_mock(url, request):
            return response(200, '{"name": "/v1/projects/TEST/topics/topic1"}', None, None, 5, request)

        with HTTMock(has_topic_mock):
            self.assertTrue(self.ams.has_topic('topic1'))

    # Test has subscription client
    def testHasSub(self):
        # Mock response for GET topic request
        @urlmatch(netloc="localhost", path="/v1/projects/TEST/subscriptions/subscription1", method="GET")
        def has_subscription_mock(url, request):
            return response(200, '{"subscriptions":[{"name":"/v1/projects/TEST/subscriptions/subscription1",\
                            "topic":"/v1/projects/TEST/topics/topic1",\
                            "ackDeadlineSeconds":"10"}]}', None, None, 5, request)

        with HTTMock(has_subscription_mock):
            self.assertTrue(self.ams.has_sub('subscription1'))

if __name__ == '__main__':
    unittest.main()