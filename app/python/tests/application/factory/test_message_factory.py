import unittest
from main.application.factory.message_factory import MessageFactory

class TestMessageFactory(unittest.TestCase):
    def test_system_message(self):
        labels = ["person", "gpe", "date"]
        expected = """
            あなたは自然言語処理におけるエキスパートです。あなたのタスクは、与えられたテキストに対して固有表現抽出を行うことです。考えられる固有表現抽出のエンティティ: (person, gpe, date).
            --"""
        self.assertEqual(MessageFactory.system_message(labels), expected)

    def test_user_message_enrich_enable(self):
        text = "テストメッセージ"
        expected = """
                次に対する生成結果を出力し、Wikipediaでエンリッチした後再度 JSON 形式で結果を取得してください: テストメッセージ
            """
        self.assertEqual(MessageFactory.user_message_enrich_enable(text), expected)

    def test_user_message_enrich_enable_メッセージなし(self):
        text = ""
        expected = """
                次に対する生成結果を出力し、Wikipediaでエンリッチした後再度 JSON 形式で結果を取得してください: 
            """
        self.assertEqual(MessageFactory.user_message_enrich_enable(text), expected)

    def test_user_message_enrich_disable(self):
        text = "テストメッセージ"
        expected = """
                次に対する生成結果を出力してください: テストメッセージ
            """
        self.assertEqual(MessageFactory.user_message_enrich_disable(text), expected)

    def test_user_message_enrich_disable_メッセージなし(self):
        text = ""
        expected = """
                次に対する生成結果を出力してください: 
            """
        self.assertEqual(MessageFactory.user_message_enrich_disable(text), expected)

if __name__ == '__main__':
    unittest.main()