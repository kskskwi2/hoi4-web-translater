import re

class ParadoxParser:
    @staticmethod
    def parse(content: str) -> dict:
        """
        Parses a Paradox script string into a Python dictionary.
        Handles key="value", key={ list }, and simple key=value.
        """
        # Remove comments
        content = re.sub(r'#.*', '', content)
        
        data = {}
        
        # Regex for key="value" or key=value
        # Matches: key = "value"  OR  key = value
        simple_pairs = re.finditer(r'(\w+)\s*=\s*(".*?"|[\w\.]+)', content)
        for match in simple_pairs:
            key = match.group(1)
            value = match.group(2)
            
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
                
            data[key] = value

        # Regex for key={ ... } (Lists/Tags)
        # This is a simple implementation for non-nested lists like tags={}
        # For full nested structure (like focus trees), a recursive parser is needed.
        # But for descriptor.mod, this usually suffices.
        list_pairs = re.finditer(r'(\w+)\s*=\s*\{([^}]+)\}', content)
        for match in list_pairs:
            key = match.group(1)
            raw_list = match.group(2)
            
            # Extract items from the list
            # Items can be quoted "Item" or unquoted Item
            items = []
            # Find all quoted strings
            items.extend(re.findall(r'"(.*?)"', raw_list))
            # Find all unquoted words (if mixed, this might duplicate, but usually tags are one or the other)
            # Actually, let's just split by whitespace and clean up
            
            # A safer way allows for mixed:
            # We want to match "String" OR Word, ignoring whitespace
            tokens = re.findall(r'"(.*?)"|(\w+)', raw_list)
            clean_items = []
            for t_quoted, t_word in tokens:
                if t_quoted:
                    clean_items.append(t_quoted)
                elif t_word:
                    clean_items.append(t_word)
            
            data[key] = clean_items
            
        return data

    @staticmethod
    def parse_file(file_path: str) -> dict:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ParadoxParser.parse(content)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return {}
