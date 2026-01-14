from sqlalchemy import text
from .database import engine


def migrate_db():
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(settings)"))
            columns = [row[1] for row in result.fetchall()]

            if "auto_shutdown" not in columns:
                print("Migrating: Adding auto_shutdown to settings table")
                conn.execute(
                    text(
                        "ALTER TABLE settings ADD COLUMN auto_shutdown BOOLEAN DEFAULT 0"
                    )
                )
                conn.commit()

            if "source_language" not in columns:
                print("Migrating: Adding source_language to settings table")
                conn.execute(
                    text(
                        "ALTER TABLE settings ADD COLUMN source_language VARCHAR(10) DEFAULT 'en'"
                    )
                )
                conn.commit()

            if "vanilla_path" not in columns:
                print("Migrating: Adding vanilla_path to settings table")
                conn.execute(
                    text("ALTER TABLE settings ADD COLUMN vanilla_path VARCHAR(512)")
                )
                conn.commit()

            if "enable_paratranz" not in columns:
                print("Migrating: Adding enable_paratranz to settings table")
                conn.execute(
                    text(
                        "ALTER TABLE settings ADD COLUMN enable_paratranz BOOLEAN DEFAULT 0"
                    )
                )
                conn.commit()

            if "glossary" not in columns:
                print("Migrating: Adding glossary to settings table")
                conn.execute(
                    text("ALTER TABLE settings ADD COLUMN glossary TEXT DEFAULT '{}'")
                )
                conn.commit()

            if "openai_model" not in columns:
                print("Migrating: Adding openai_model to settings table")
                conn.execute(
                    text(
                        "ALTER TABLE settings ADD COLUMN openai_model VARCHAR(255) DEFAULT 'gpt-4o-mini'"
                    )
                )
                conn.commit()

            if "claude_model" not in columns:
                print("Migrating: Adding claude_model to settings table")
                conn.execute(
                    text(
                        "ALTER TABLE settings ADD COLUMN claude_model VARCHAR(255) DEFAULT 'claude-3-5-sonnet-20241022'"
                    )
                )
                conn.commit()

            if "gemini_model" not in columns:
                print("Migrating: Adding gemini_model to settings table")
                conn.execute(
                    text(
                        "ALTER TABLE settings ADD COLUMN gemini_model VARCHAR(255) DEFAULT 'gemini-1.5-flash'"
                    )
                )
                conn.commit()

            if "auto_upload_paratranz" not in columns:
                print("Migrating: Adding auto_upload_paratranz to settings table")
                conn.execute(
                    text(
                        "ALTER TABLE settings ADD COLUMN auto_upload_paratranz BOOLEAN DEFAULT 0"
                    )
                )
                conn.commit()

            print("Migration successful")
        except Exception as e:
            print(f"Migration failed (might already exist): {e}")


if __name__ == "__main__":
    migrate_db()
