class MessageFactory:
    @staticmethod
    def system_message(labels):
        return f"""
            あなたは自然言語処理におけるエキスパートです。あなたのタスクは、与えられたテキストに対して固有表現抽出を行うことです。考えられる固有表現抽出のエンティティ: ({", ".join(labels)}).
            --"""

    @staticmethod
    def assisstant_message():
        return f"""
            例:
                text: 'ドイツでは、1440年に金細工師のヨハネス・グーテンベルクが可動式印刷機を発明しました。彼の仕事は、情報革命と前例のない大衆の普及につながりました。
                ヨーロッパ全土の文学の。既存のスクリュープレスの設計をモデルにしたルネッサンス期の可動式印刷機1台で、1営業日あたり最大3,600ページを印刷できました。'
                {{
                    "gpe": ["ドイツ", "ヨーロッパ"],
                    "date": ["1440"],
                    "person": ["ヨハネス・グーテンベルク"],
                    "product": ["可動式印刷機"],
                    "event": ["ルネッサンス"],
                    "quantity": ["3,600ページ"],
                    "time": ["1営業日"]
                }}
            --"""

    @staticmethod
    def user_message_enrich_enable(text):
        return f"""
                次に対する生成結果を出力し、Wikipediaでエンリッチした後再度 JSON 形式で結果を取得してください: {text}
            """

    @staticmethod
    def user_message_enrich_disable(text):
        return f"""
                次に対する生成結果を出力してください: {text}
            """