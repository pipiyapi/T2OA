from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
llm = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key='sk-wOXat7SFftYVnBeODe35991dAcCf487c9833F7E3025f0f9c',
    openai_api_base='https://api.gpt.ge/v1/',
    max_tokens=10000
)
llm_R1 = ChatOpenAI(
    model='deepseek-reasoner',
    openai_api_key='*****************',
    openai_api_base='*****************',
    max_tokens=8000
)
llm_split_prompt = ChatPromptTemplate.from_template("""
    <Role>
    你是文本分块专家，下面的chunk是为两个原本相连的文本块，请判断如果按照当前位置划分为chunk1和chunk2是否合理。
    </Role>
    
     <requirement>
    1.理解文本内容。
	2.你只需要对chunk1末尾和chunk2开头的分块位置判断，不需要判断chunk1开头和chunk2末尾。
    3.如果你认为当前分块位置合理，分块后chunk1和chunk2可以单独理解，规范条目完整存在于同一块内，返回1。
    4.如果你认为当前分块位置不合理，分块后chunk1和chunk2无法单独理解，上下文语义被破坏，同一规范条目不在同一块内则返回0。
    5.结果只返回1或0，除此之外不要返回其他任何内容
    </requirement>
    
    <chunk1>
    {chunk1}
    </chunk1>

    <chunk2>
    {chunk2}
    </chunk2>
    """)
ner1_prompt = ChatPromptTemplate.from_template("""
    <Role>
    你是绿色建筑评估领域专门进行知识图谱中的实体抽取的专家。
    </Role>

    <task>
    请从下面给出的绿色建筑规范文本中抽取出实体并生成其实体类型，结果以json格式的列表返回[[实体1，实体类型1],[实体2，实体类型2].....[实体n，实体类型n]],除此之外不要返回其他任何内容。
    <task>

    <requirement>
    -你需要理解文本内容，不要遗漏任何一个实体
    -规范条文的编号不要作为实体抽取。
    -实体类型应该是从文本中抽取的实体的抽象上位词
    </requirement>

    <text>
    以下是你需要进行实体抽取的文本：
    {text}
    </text>
    """)
ner2_prompt = ChatPromptTemplate.from_template("""
    <Role>
    你是绿色建筑评估领域专门进行知识图谱中的实体抽取的专家。
    </Role>

    <task>
    entity_list中内容为已经抽取出的实体。请根据text中的内容对entity_list中的错误的[实体,实体类型]进行替换，正确的[实体,实体类型]进行保留，遗漏的[实体,实体类型]进行追加。结果以json格式的列表返回最终完整的[[实体1，实体类型1],[实体2，实体类型2].....[实体n，实体类型n]],除此之外不要返回其他任何内容。
    <task>

    <requirement>
    -你需要理解文本内容，不要遗漏任何一个实体
    -规范条文的编号不要作为实体抽取。
    -实体类型应该是从文本中抽取的实体的抽象上位词
    </requirement>

    <text>
    以下是你需要进行实体抽取的文本：
    {text}
    </text>

    <entity_list>
    {entity_list}
    </entity_list>
    """)
llm_disambiguation_prompt = ChatPromptTemplate.from_template(
    """
    <Role>
    你是绿色建筑领域构建本体模型的专家，你熟悉各种绿色建筑领域的专业名词,能够区分不同专业名词的含义。
    </Role>
    
    <Task>
    你的目标是根据给出的实体类型列表，找出含义相同的实体类型，找出的实体类型只是名称不同，但是指代的对象和描述的范围一致，本质上属于同一个实体类型。结构必须以return_json中所示的json格式返回。
    </Task>
    
    <thinking_step>
    -理解给出的entity_type_list中每个实体类型具体含义，并明确指代边界。
    -找出你认为含义相同的实体类型
    -对每组找出的实体类型放入返回的json列表中，返回格式return_json中所示，除此之外不要返回其他任何内容。
    </thinking_step>

    <example>
    1.'指标', '用水量指标' 解释：指标的概念比用水量指标更广泛，因此不属于同一实体类型。
    2.'污染物', '危险物质' 解释：污染物指的是对环境造成影响的物质，而危险物质则是对人体健康造成影响的物质，因此不属于同一实体类型。
    3.'标准', '标准规范'  解释：标准和标准规范都是只建筑领域的标准条文规范，因此属于同一实体类型。
    4.'植物', '植物类型' 解释：植物和植物类型都是指植物的种类，因此属于同一实体类型。
    </example>
    
    <return_json>
    [[实体类型1,实体类型2,....],[实体类型3,实体类型4,实体类型5,...],......]
    </return_json>

    <entity_type_list>
    以下是给出的实体类型列表:
    {entity_type_list}
    </entity_type_list>
            
    """
)
llm_disambiguation_diagnose_prompt = ChatPromptTemplate.from_template(
    """
    <task>
    你是绿色建筑领域进行本体模型构建的专家，以下给出多个实体类型，他们的被初步认为只是名称不同，但是指代的对象和描述的范围一致，本质上属于同一个实体类型，请结合我给出的entity_type_description_info中实体类型相关信息帮我判断是否合理。
    </task>

    <thinking_step>
    如果你认为给出的实体类型只是名称不同，但是指代的对象和描述的范围一致，本质上属于同一个实体类型，则说明理由,然后选择给出的实体类型中的一个作为消歧后的实体类型并调用tool_disambiguation工具。
    如果你认为这些实体类型完全没有任何关系，完全是无关概念，不需要进行消歧义，则说明理由并调用tool_not_disambiguation工具，
    </thinking_step>

    <same_entity_type_rule>
    -相同的实体类型具有相同的实体。
    -相同的实体类型之间不是is_a关系，属于同一层级。
    -相同的实体类型具有相似的描述。
    </same_entity_type_rule>
   
    <example>
    1.'指标', '用水量指标' 解释：指标的概念比用水量指标更广泛，因此不属于同一实体类型。
    2.'污染物', '危险物质' 解释：污染物指的是对环境造成影响的物质，而危险物质则是对人体健康造成影响的物质，因此不属于同一实体类型。
    3.'标准', '标准规范'  解释：标准和标准规范都是只建筑领域的标准条文规范，因此属于同一实体类型。
    4.'植物', '植物类型' 解释：植物和植物类型都是指植物的种类，因此属于同一实体类型
    </example>

    <requirement>
    -你一次只能调用一种工具。
    -根据same_entity_type_rule中的规则判断是否属于同一实体类型。
    -请为你调用的工具提供准确的输入
    -消歧后的实体类型只能是给出的实体类型中的一个。
    </requirement>

    <entity_type_description_info>
    以下是多个实体类型的相关信息，帮助你判断多个实体类型是否能消歧为同一个实体类型：
    {entity_type_description}
    </entity_type_description_info>

    <entity_type>
    以下是你需要判断的实体类型：{entity_type_list}
    </entity_type>
    """
)

llm_add_relation_prompt = ChatPromptTemplate.from_template(
            """
            <Role>
            你是绿色建筑领域构建本体模型的专家，你熟悉各种绿色建筑领域的专业名词,能够区分不同专业名词的含义。
            </Role>
            
            <Task>
            你的目标是根据给出的实体类型列表，找出含义相似的实体类型，并且你找出的实体类型可能存在以下两种情况之一：
            1.实体类型间存在is_a的关系，即存在找出的实体类型其中一个是另一个的子类或父类，只能是两个实体类型。
            2.找出的实体类型属于同一个层级，即同属于同一个父类之下，两个或以上实体类型。
            </Task>
            
            <thinking_step>
            -理解给出的entity_type_list中每个实体类型具体含义，并明确指代边界。
            -找出属于task中两种情况的实体类型。
            -找出的实体类型来源只能是entity_type_list,不能够由你生成：
            -对每组找出的实体类型放入返回的json字典的对应列表中，返回格式return_json中所示，除此之外不要返回其他任何内容。
            </thinking_step>
            
            <example>
            1. '指标', '用水量指标' 解释：指标的概念比用水量指标更广泛，指标除了包含用水量指标还包含其他指标，因此属于is_a关系。
            2. '医疗设施','教育设施','文化设施','健身设施' 解释：医疗设施、教育设施、文化设施、健身设施都是并列关系，属于同一层级，能够具有同一上位词'建筑设施'
            3. '混凝土类型','钢材类型' 解释：混凝土类型、钢材类型都是并列关系，属于同一层级，能够具有同一上位词'建筑材料'
            4.  '自然条件' , '土壤条件' 解释：自然条件概念比土壤条件更广泛，自然条件除了包含土壤条件还包含其他条件，因此属于is_a关系。
            </example>
            
            <return_json>
            {{
            "is_a":[[实体类型1,实体类型2],[实体类型3,实体类型4],......],
            "same_level_entity_type":[[实体类型5,实体类型6,....],[实体类型7,实体类型8,实体类型9,....],......],
            }}
            </return_json>
            
            <Requirements>
            -一个实体类型多次出现在不同情况中
            -你只需要考虑最合理输出，不需要让entity_type_list中的所有实体类型被处理。
            </Requirements>
            
            <entity_type_list>
            以下是未处理的实体类型列表:
            {entity_type_list}
            </entity_type_list>
            """
)
llm_is_a_diagnose_prompt = ChatPromptTemplate.from_template(
    """
    <task>
    你是绿色建筑领域进行本体模型构建的专家，以下给出两个实体类型，他们的被初步认为之间存在is_a的关系，即存在其中一个实体类型是另一个的子类或父类，请结合我给出的entity_type_description_info中实体类型相关信息帮我判断是否合理。
    </task>
    
    <thinking_step>
    如果你认为两个实体类型存在is_a关系，即存在其中一个实体类型是另一个的子类或父类，则说明理由并调用tool_is_a工具
    如果你认为两个实体类型完全没有任何关系，完全是两个无关概念，则说明理由并调用tool_not_handle工具，
    </thinking_step>
    
    <requirement>
    -你一次只能调用一种工具。
    -根据is_a_rule中的规则判断是否存在is_a关系
    -请为你调用的工具提供准确的输入
    -调用工具的输入必须包含所有给出的entity_type中的实体类型，不能只取一部分作为输入。
    </requirement>
    
    <is_a_rule>
    -形成is_a关系的实体类型中，父类的概念比子类的概念更广泛。
    -形成is_a关系的两个实体类型之间不是同一层级，即不是同属于同一个父类之下。
    </is_a_rule>
    
    <entity_type_description_info>
    以下是两个实体类型的相关信息，帮助你判断两个实体类型是否存在is_a关系：
    {entity_type_description}
    </entity_type_description_info>

    <entity_type>
    以下是你需要判断的实体类型：{entity_type_list}
    </entity_type>
    """
)
llm_hypernym_generation_diagnose_prompt = ChatPromptTemplate.from_template(
    """
    <task>
    你是绿色建筑领域进行本体模型构建的专家，以下给出多个实体类型，他们的被初步认为属于同一个层级，即同属于同一个父类之下，请结合我给出的entity_type_description_info中实体类型相关信息帮我判断是否合理。
    </task>

    <thinking_step>
    如果你认为给出实体类型属于同一个层级，即同属于同一个父类之下，则说明理由，然后生成一个父类上位词并调用tool_hypernym_generation工具。
    如果你认为这些实体类型完全没有任何关系，完全是无关概念，则说明理由并调用tool_not_handle工具，
    </thinking_step>

    <requirement>
    -你一次只能调用一种工具。
    -根据same_level_entity_type_rule中的规则判断是否属于同一个层级。
    -请为你调用的工具提供准确的输入
    -调用工具的输入必须包含所有给出的entity_type中的实体类型，不能只取一部分作为输入。
    </requirement>

    <same_level_entity_type_rule>
    -相同层级的实体类型具有相同的上位词。
    -相同层级的实体类型之间不是is_a关系
    -相同层级的实体类型描述的概念必须没有交集
    </same_level_entity_type_rule>
    
    <entity_type_description_info>
    以下是多个实体类型的相关信息，帮助你判断这些实体类型是否属于同一个层级：
    {entity_type_description}
    </entity_type_description_info>

    <entity_type>
    以下是你需要判断的实体类型：{entity_type_list}
    </entity_type>
    """
)
llm_cluster_labeling_prompt = ChatPromptTemplate.from_template(
    """
    <task>
    你是绿色建筑领域进行本体模型构建的专家，给定一个特定主题的集群，您的任务是确定一个包含集群中所有主题的更广泛的概念或类别。这个更广泛的概念被称为本体标签。标签表示包含所有主题的一般类别。
    </task>

    <requirement>
    结果只返回你生成的本体标签，除此之外不要返回其他任何内容。
    </requirement>
    
    以下是给出的主题集群：
    {topic_cluster}
    """
)
llm_fix_graph_prompt = ChatPromptTemplate.from_template(
    """
    <task>
    你是绿色建筑领域构建本体模型的专家，你现在需要构建一个有向无环的树状本体模型图，接下来我会给出一些不符合有向无环的树状图要求的结构混乱的子图json格式表示，你需要帮我修复这些子图，使其符合有向无环的树状图要求。
    </task>
    
    <think_step>
    -理解给出的nodes中的每一个实体类型含义以及其指代边界，不要遗漏任何实体类型。
    -理解给出的edges中的每一个关系边的含义，不要遗漏任何关系边。
    -理解requirement中对修改后的图的结构要求，对不符合要求的关系进行修改，同时需要确保每一个关系合理正确。
    -以如return_json中所示json格式返回，除此之外不要返回其他任何内容。
    </think_step>
    
    <requirement>
    -你只能对图中的关系边进行修改，不能增加和删除节点。
    -你需要保证返回的图结构是有向无环的树状图结构，即每个节点的出度不大于1，并且没有环。
    -你需要保证修改后的关系合理正确，存在关系的两个节点是is_a关系，即头节点是尾节点的子类，尾节点是头节点的父类。
    -你需要尽可能避免过深的子树结构，即每个节点的深度不超过4。
    -你需要避免语义矛盾循环的情况，例如：建筑设备->排水设备->设备设施，建筑设备与设施设备描述概念范围都比排水设备更广泛，存在循环，并且关系不合理。
    -修改后结果以如return_json中所示格式返回，除此之外不要返回其他任何内容。
    -你需要尽可能满足ontology_rule中一个良好的本体模型要求。
    </requirement>
    
    <ontology_rule>
    -清晰定义：概念和关系必须明确无歧义。
    -逻辑一致：避免矛盾公理和循环定义。
    -可扩展设计：采用模块化结构，预留扩展点并遵循开放世界假设。
    -形式化表达：明确定义公理和约束规则。
    -语义丰富：支持自动推理，构建层次化分类和精细化关系。
    -可重用性：能够复用已有本体，遵循领域最佳实践以减少重复开发。
    </ontology_rule>
    
    
    <json_graph_info>
    以下是给出你需要修改的子图json格式表示：
    {json_graph_info}
    </json_graph_info>
    
    <return_json>
    {{
    "nodes":[实体类型1,实体类型2,......],
    "edges":[{{"from": 实体类型1, "relation": "is_a", "to": 实体类型'}}，{{"from": 实体类型3,"relation": "is_a", "to": 实体类型4}}，......]
    }}
    </return_json>
    """
)
llm_schema_prompt = ChatPromptTemplate.from_template(
    """
    你是绿色建筑领域构建本体模型的专家，你现在需要用自顶向下和自底向上的方式构建一个具有层次树状结构的本体模型，你现在需要理解我给出的多个实体类型，然后从中提炼出能够概括这些实体类型的上位词，要求上位词应该尽可能覆盖给出的实体类型，不要遗漏。结果返回你生成的上位词，然后每个上位词后举例列举5-7个实体类型
    以下是给出的实体类型列表：
    {in_graph_all_node}
    """
)
llm_json_format_prompt = ChatPromptTemplate.from_template(
    """
    你是一个将文本转为json格式的专家，你需要将给出的文本转化为json格式。
    给出的文本是一段关于本体模型层次结构的描述，你需要帮我将其转为字典表。

    以下是json格式要求：
    {{"一级实体列表":[一级实体类型1，一级实体类型2，...，一级实体类型n]，
    "一级实体列表字典表":{{一级实体类型1:[二级实体类型1，二级实体类型2，...，二级实体类型n],一级实体类型2:[二级实体类型1，二级实体类型2，...，二级实体类型n],...}}
    }}

    结果只返回你转化后的json格式字典表，除此之外不要返回其他任何解释。

    以下是你需要进行处理的文本：
    {schema_result}
    """
)
llm_is_a_schema_prompt = ChatPromptTemplate.from_template(
    """
    <task>
    你是绿色建筑领域构建本体模型的专家，你需要判断我给出的实体类型与给出的上位词列表中的一个上位词形成is_a关系，返回你选择的上位词，除此之外不要返回其他任何内容。
    </task>
    
    <step>
    -理解Hypernym_list中我给出的每个上位词的表示范围，example中是一些能够与上位词形成is_a关系的示例。
    -如果该实体类型与example中的示例含义相似，则可能与该对应上位词存在is_a关系。
    -将实体类型与上位词列表中的每个上位词进行比较，判断它们之间是否存在is_a关系。
    -如果存在is_a关系，返回你选择的上位词，除此之外不要返回其他任何内容。
    </step>
    
    <example>
    以下是一些能够与上位词形成is_a关系的示例：
    {schema_example}
    </example>
    
    <Hypernym_list>
    以下是你需要选择的上位词列表：
    {Hypernym_list}
    </Hypernym_list>
    
    <entity_type>
    以下是你需要判断是否能和上位词列表中的词语形成is_a关系的实体类型：
    {entity_type}
    </entity_type>
    """
)


Hypernym_disambiguation_prompt = ChatPromptTemplate.from_template(
    """
    <task>
    你是绿色建筑领域进行实体类型消歧的专家，你需要对给出的entity_type进行判断是否与给出related_nodes中的某一个实体类型含义一致。
    </task>
    
    <thinking_step>
    -理解给出的entity_type具体含义，并明确指代边界。
    -理解给出的related_nodes中每个实体类型具体含义，并明确指代边界。
    -思考entity_type与related_nodes中哪一个实体类型指代的对象范围一致含义相同。
    -选择related_nodes中一个实体类型作为结果返回。
    </thinking_step>

    <Requirements>
    -你需要保证结果返回的实体类型与entity_type指代的对象范围一致含义相同。
    -结果你只需要返回你选择related_nodes中的实体类型，不要返回其他任何内容，不要解释。
    </Requirements>
    
    <entity_type>
    以下是你需要进行判断的实体类型：
    {entity_type}
    </entity_type>

    <related_nodes>
    以下是你需要判断entity_type与哪个实体类型含义一致的实体类型列表：
    {related_nodes}
    </related_nodes>
    """
)
Hypernym_disambiguation_diagnose_prompt=ChatPromptTemplate.from_template(
    """
     <task>
    你是绿色建筑领域进行本体模型构建的专家，以下给出多个实体类型，他们的被初步认为只是名称不同，但是指代的对象和描述的范围一致，本质上属于同一个实体类型，请结合我给出的entity_type_description_info中实体类型相关信息帮我判断是否合理。
    </task>

    <thinking_step>
    如果你认为给出的实体类型只是名称不同，但是指代的对象和描述的范围一致，本质上属于同一个实体类型，则输出一个消歧后的实体类型。
    如果你认为这些实体类型完全没有任何关系，完全是无关概念，不需要进行消歧义，则输出"消歧失败"。
    </thinking_step>

    <requirement>
    -结构只返回消歧后的实体类型或"消歧失败"，除此之外不要返回其他任何内容。
    </requirement>

    <entity_type_description_info>
    以下是多个实体类型的相关信息，帮助你判断多个实体类型是否能消歧为同一个实体类型：
    {entity_type_description}
    </entity_type_description_info>

    <entity_type>
    以下是你需要判断的实体类型：{entity_type_list}
    </entity_type>
    """
)

tree_format_prompt = ChatPromptTemplate.from_template("""
你是将三元组转化为层次结构的格式专家，你需要对给出的多个三元组进行格式转化，转化为层次结构清晰的格式表示。

<Requirements>
-一个三元组中尾节点是头节点的父类，父类和子类用|—的符号链接，|—的符号链接的两端必须在一个三元组中，不要跨越层级。
-结构只返回转化后的格式内容，不要解释
-不要遗漏任何一个节点
</Requirements>

<triple_list>
以下是你要转化格式的三元组列表:
{triple_list}
</triple_list>
""")
llm_evaluate_prompt = ChatPromptTemplate.from_template(
    """
    <Role>
    你是绿色建筑领域的专家，你熟悉各种绿色建筑领域的专业名词,能够区分不同专业名词的含义。
    </Role>

    <Task>
    你现在需要对我给出的句子进行判断，如果你认为正确返回"true"，如果你认为错误返回"false",除此之外不要返回其他任何内容。
    </Task>
    
    <sentence>
    以下是你需要进行判断的句子：
    {entity}是{entity_type}中的一种，{entity_type}包含有{entity}。
    </sentence>
    """
)
