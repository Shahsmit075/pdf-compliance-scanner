import os
import textwrap

for root, dirs, files in os.walk('app'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()

            import re
            
            # Add import textwrap if not present
            if 'import textwrap' not in content and 'st.markdown(' in content:
                content = content.replace('import streamlit as st', 'import streamlit as st\nimport textwrap')

            # We need to wrap string literals inside st.markdown(..., unsafe_allow_html=True) with textwrap.dedent
            # The regex looks for st.markdown( f\"\"\"...\"\"\", unsafe_allow_html=True ) and wraps the string.
            # Actually, the safest way is to just use textwrap.dedent on all of them.
            content = re.sub(
                r'st\.markdown\(\s*(f?"""[\s\S]*?""")\s*,\s*unsafe_allow_html=True\s*\)',
                r'st.markdown(textwrap.dedent(\1), unsafe_allow_html=True)',
                content
            )
            
            content = re.sub(
                r'st\.markdown\(\s*(f?\'\'\'[\s\S]*?\'\'\')\s*,\s*unsafe_allow_html=True\s*\)',
                r'st.markdown(textwrap.dedent(\1), unsafe_allow_html=True)',
                content
            )

            with open(path, 'w') as f:
                f.write(content)
