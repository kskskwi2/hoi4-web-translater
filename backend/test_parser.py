from app.services.parser import ParadoxParser

test_content = '''
version="1.0"
tags={
	"Fixes"
	"Balance"
	"Gameplay"
	"Technologies"
}
name="Refit It!"
picture="thumbnail.png"
supported_version="1.17.*"
remote_file_id="2915924276"
'''

def test():
    print("Testing ParadoxParser...")
    result = ParadoxParser.parse(test_content)
    print("Result:", result)
    
    assert result['name'] == "Refit It!"
    assert "Fixes" in result['tags']
    assert result['remote_file_id'] == "2915924276"
    print("Test Passed!")

if __name__ == "__main__":
    test()
