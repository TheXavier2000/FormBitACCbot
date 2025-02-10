from notion_client import Client

NOTION_TOKEN = "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"
DATABASE_ID = "28b23c45-196c-4646-a437-d83a07874d62"

notion = Client(auth=NOTION_TOKEN)

def actualizar_notion(mensaje):
    notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties={
            "Mensaje": {"title": [{"text": {"content": mensaje}}]}
        }
    )
    print("Datos enviados a Notion")
