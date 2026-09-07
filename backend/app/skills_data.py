"""Static knowledge base: roles, required skills, learning resources, and sample
opportunities for the Pakistani job market. Acts as the rule-based 'AI' data layer
that the recommendation engine (skills_engine.py) reasons over."""

# ---------------------------------------------------------------------------
# Master skill dictionary: canonical_name -> (category, [aliases used for CV/text matching])
# categories: technical | soft | tool | certification
# ---------------------------------------------------------------------------
SKILL_DICTIONARY = {
    "HTML": ("technical", ["html", "html5"]),
    "CSS": ("technical", ["css", "css3"]),
    "JavaScript": ("technical", ["javascript", "js", "es6"]),
    "TypeScript": ("technical", ["typescript", "ts"]),
    "React": ("tool", ["react", "reactjs", "react.js"]),
    "Vue.js": ("tool", ["vue", "vuejs", "vue.js"]),
    "Angular": ("tool", ["angular", "angularjs"]),
    "Node.js": ("tool", ["node", "nodejs", "node.js", "express", "expressjs"]),
    "Python": ("technical", ["python", "py"]),
    "Django": ("tool", ["django"]),
    "Flask": ("tool", ["flask"]),
    "FastAPI": ("tool", ["fastapi"]),
    "Java": ("technical", ["java"]),
    "Spring Boot": ("tool", ["spring", "spring boot", "springboot"]),
    "C++": ("technical", ["c++", "cpp"]),
    "C#": ("technical", ["c#", "csharp"]),
    "PHP": ("technical", ["php"]),
    "SQL": ("technical", ["sql", "mysql", "postgresql", "postgres"]),
    "MongoDB": ("tool", ["mongodb", "mongo", "nosql"]),
    "Git": ("tool", ["git", "github", "gitlab", "version control"]),
    "Docker": ("tool", ["docker", "containers", "containerization"]),
    "Kubernetes": ("tool", ["kubernetes", "k8s"]),
    "AWS": ("tool", ["aws", "amazon web services"]),
    "Linux": ("technical", ["linux", "unix", "bash"]),
    "REST APIs": ("technical", ["rest", "rest api", "restful", "api development"]),
    "Data Structures & Algorithms": ("technical", ["dsa", "data structures", "algorithms"]),
    "Machine Learning": ("technical", ["machine learning", "ml"]),
    "Deep Learning": ("technical", ["deep learning", "neural networks", "dl"]),
    "TensorFlow": ("tool", ["tensorflow", "tf"]),
    "PyTorch": ("tool", ["pytorch"]),
    "Pandas": ("tool", ["pandas"]),
    "NumPy": ("tool", ["numpy"]),
    "Scikit-learn": ("tool", ["scikit-learn", "sklearn"]),
    "NLP": ("technical", ["nlp", "natural language processing"]),
    "Data Visualization": ("technical", ["data visualization", "tableau", "power bi", "powerbi"]),
    "Statistics": ("technical", ["statistics", "statistical analysis"]),
    "Excel": ("tool", ["excel", "ms excel", "spreadsheets"]),
    "Cybersecurity Fundamentals": ("technical", ["cybersecurity", "cyber security", "infosec"]),
    "Network Security": ("technical", ["network security", "networking"]),
    "Penetration Testing": ("technical", ["penetration testing", "pentesting", "ethical hacking"]),
    "SIEM Tools": ("tool", ["siem", "splunk"]),
    "Wireshark": ("tool", ["wireshark"]),
    "Nmap": ("tool", ["nmap"]),
    "Metasploit": ("tool", ["metasploit"]),
    "Cryptography": ("technical", ["cryptography", "encryption"]),
    "Flutter": ("tool", ["flutter", "dart"]),
    "React Native": ("tool", ["react native"]),
    "Kotlin": ("technical", ["kotlin"]),
    "Swift": ("technical", ["swift"]),
    "Android Studio": ("tool", ["android studio", "android sdk"]),
    "Xcode": ("tool", ["xcode", "ios development"]),
    "Figma": ("tool", ["figma"]),
    "Adobe XD": ("tool", ["adobe xd", "axure"]),
    "Wireframing": ("technical", ["wireframing", "wireframes"]),
    "Prototyping": ("technical", ["prototyping", "prototype design"]),
    "User Research": ("technical", ["user research", "usability testing"]),
    "Design Systems": ("technical", ["design systems"]),
    "Communication": ("soft", ["communication", "communication skills"]),
    "Teamwork": ("soft", ["teamwork", "collaboration"]),
    "Problem Solving": ("soft", ["problem solving", "critical thinking"]),
    "Time Management": ("soft", ["time management"]),
    "Leadership": ("soft", ["leadership", "team lead"]),
    "Adaptability": ("soft", ["adaptability", "flexibility"]),
    "AWS Certified Cloud Practitioner": ("certification", ["aws certified"]),
    "Google Data Analytics Certificate": ("certification", ["google data analytics"]),
    "CompTIA Security+": ("certification", ["security+", "comptia"]),
    "PMP": ("certification", ["pmp", "project management professional"]),
    "Bash Scripting": ("technical", ["bash", "shell scripting"]),
    "CI/CD Pipelines": ("tool", ["ci/cd", "cicd", "jenkins", "github actions"]),
    "Terraform": ("tool", ["terraform", "infrastructure as code", "iac"]),
    "Ansible": ("tool", ["ansible"]),
    "Networking Fundamentals": ("technical", ["networking", "computer networks", "tcp/ip"]),
    "Manual Testing": ("technical", ["manual testing", "test cases"]),
    "Automation Testing": ("technical", ["automation testing", "test automation"]),
    "Selenium": ("tool", ["selenium"]),
    "API Testing": ("technical", ["api testing", "postman"]),
    "Content Writing": ("technical", ["content writing", "copywriting"]),
    "SEO": ("technical", ["seo", "search engine optimization"]),
    "Social Media Marketing": ("technical", ["social media marketing", "smm"]),
    "Google Analytics": ("tool", ["google analytics", "ga4"]),
    "Google Ads": ("tool", ["google ads", "adwords"]),
    "Business Analysis": ("technical", ["business analysis", "requirements gathering"]),
    "Agile/Scrum": ("technical", ["agile", "scrum"]),

    # --- Shared engineering foundations ---
    "Engineering Mathematics": ("technical", ["engineering mathematics", "engineering maths", "calculus"]),
    "Engineering Mechanics": ("technical", ["engineering mechanics", "statics", "dynamics"]),
    "Engineering Drawing": ("technical", ["engineering drawing", "technical drawing", "drafting"]),
    "AutoCAD": ("tool", ["autocad", "auto cad"]),
    "Project Planning": ("technical", ["project planning", "primavera", "ms project"]),
    "Quality Control": ("technical", ["quality control", "qa/qc", "quality assurance"]),

    # --- Civil Engineering ---
    "Structural Analysis": ("technical", ["structural analysis"]),
    "Reinforced Concrete Design": ("technical", ["reinforced concrete", "rcc design", "concrete design"]),
    "Steel Structure Design": ("technical", ["steel structure", "steel design"]),
    "ETABS": ("tool", ["etabs"]),
    "STAAD Pro": ("tool", ["staad pro", "staad.pro", "staad"]),
    "Civil 3D": ("tool", ["civil 3d", "civil3d"]),
    "Earthquake Engineering": ("technical", ["earthquake engineering", "seismic design"]),
    "Surveying": ("technical", ["surveying", "land surveying", "total station"]),
    "Construction Management": ("technical", ["construction management"]),
    "Estimation & Costing": ("technical", ["estimation", "costing", "quantity surveying"]),
    "Site Supervision": ("technical", ["site supervision", "site engineer"]),
    "Building Codes": ("technical", ["building codes", "building code"]),
    "Transportation Engineering": ("technical", ["transportation engineering"]),
    "Highway Design": ("technical", ["highway design", "road design"]),
    "Traffic Engineering": ("technical", ["traffic engineering"]),
    "Geotechnical Engineering": ("technical", ["geotechnical", "soil mechanics"]),

    # --- Mechanical Engineering ---
    "SolidWorks": ("tool", ["solidworks", "solid works"]),
    "CATIA": ("tool", ["catia"]),
    "ANSYS": ("tool", ["ansys"]),
    "Machine Design": ("technical", ["machine design", "mechanical design"]),
    "Material Science": ("technical", ["material science", "materials science", "strength of materials"]),
    "Finite Element Analysis": ("technical", ["finite element analysis", "fea"]),
    "Thermodynamics": ("technical", ["thermodynamics"]),
    "Fluid Mechanics": ("technical", ["fluid mechanics", "fluid dynamics"]),
    "Heat Transfer": ("technical", ["heat transfer"]),
    "HVAC Design": ("technical", ["hvac design", "hvac"]),
    "Revit MEP": ("tool", ["revit mep", "revit"]),
    "Energy Auditing": ("technical", ["energy auditing", "energy audit"]),
    "Manufacturing Processes": ("technical", ["manufacturing processes", "manufacturing"]),
    "CNC Machining": ("technical", ["cnc machining", "cnc"]),
    "Lean Manufacturing": ("technical", ["lean manufacturing", "lean"]),
    "Six Sigma": ("technical", ["six sigma"]),

    # --- Electrical Engineering ---
    "Circuit Analysis": ("technical", ["circuit analysis", "circuit design", "circuits"]),
    "Electrical Machines": ("technical", ["electrical machines", "motors and generators"]),
    "Power Systems": ("technical", ["power systems", "power system"]),
    "Power Electronics": ("technical", ["power electronics"]),
    "MATLAB": ("tool", ["matlab", "simulink"]),
    "Renewable Energy Systems": ("technical", ["renewable energy", "solar energy", "solar pv"]),
    "High Voltage Engineering": ("technical", ["high voltage", "hvdc"]),
    "SCADA": ("tool", ["scada"]),
    "Digital Electronics": ("technical", ["digital electronics", "digital logic"]),
    "Analog Electronics": ("technical", ["analog electronics"]),
    "Microcontrollers": ("technical", ["microcontrollers", "arduino", "8051", "avr"]),
    "PCB Design": ("technical", ["pcb design", "pcb", "altium"]),
    "Embedded Systems": ("technical", ["embedded systems", "embedded c"]),
    "Signal Processing": ("technical", ["signal processing", "dsp"]),
    "IoT": ("technical", ["iot", "internet of things"]),
    "PLC Programming": ("technical", ["plc programming", "plc", "ladder logic"]),
    "Control Systems": ("technical", ["control systems", "control theory"]),
    "Industrial Automation": ("technical", ["industrial automation", "automation"]),
    "Robotics": ("technical", ["robotics", "ros"]),

    # --- Business & Finance ---
    "Accounting": ("technical", ["accounting", "financial accounting"]),
    "Bookkeeping": ("technical", ["bookkeeping"]),
    "Financial Reporting": ("technical", ["financial reporting", "financial statements"]),
    "Taxation": ("technical", ["taxation", "tax"]),
    "QuickBooks": ("tool", ["quickbooks", "quick books"]),
    "Auditing": ("technical", ["auditing", "audit"]),
    "Cost Accounting": ("technical", ["cost accounting"]),
    "SAP": ("tool", ["sap", "sap erp"]),
    "Financial Analysis": ("technical", ["financial analysis"]),
    "Financial Modeling": ("technical", ["financial modeling", "financial modelling"]),
    "Valuation": ("technical", ["valuation", "dcf"]),
    "Risk Management": ("technical", ["risk management"]),
    "Human Resource Management": ("technical", ["human resource management", "hr management", "hrm"]),
    "Recruitment": ("technical", ["recruitment", "talent acquisition", "hiring"]),
    "Payroll Management": ("technical", ["payroll", "payroll management"]),
    "Employee Relations": ("technical", ["employee relations"]),
    "HR Analytics": ("technical", ["hr analytics", "people analytics"]),
    "Organizational Development": ("technical", ["organizational development", "od"]),
}

# ---------------------------------------------------------------------------
# Required skills per target role, split into roadmap phases.
# ---------------------------------------------------------------------------
ROLES = {
    "Software Engineer": {
        "beginner": ["HTML", "CSS", "JavaScript", "Git", "Data Structures & Algorithms"],
        "intermediate": ["Python", "SQL", "REST APIs", "Linux"],
        "advanced": ["Docker", "AWS", "Kubernetes"],
    },
    "Web Developer": {
        "beginner": ["HTML", "CSS", "JavaScript", "Git"],
        "intermediate": ["React", "Node.js", "REST APIs", "SQL"],
        "advanced": ["MongoDB", "Docker", "AWS"],
    },
    "Full Stack Developer": {
        "beginner": ["HTML", "CSS", "JavaScript", "Git"],
        "intermediate": ["React", "Node.js", "MongoDB", "SQL"],
        "advanced": ["Docker", "AWS", "Kubernetes"],
    },
    "Data Analyst": {
        "beginner": ["Excel", "SQL", "Statistics"],
        "intermediate": ["Python", "Pandas", "Data Visualization"],
        "advanced": ["Machine Learning", "NumPy"],
    },
    "Cybersecurity Analyst": {
        "beginner": ["Cybersecurity Fundamentals", "Network Security", "Linux"],
        "intermediate": ["Wireshark", "Nmap", "SIEM Tools"],
        "advanced": ["Penetration Testing", "Metasploit", "Cryptography", "CompTIA Security+"],
    },
    "AI Engineer": {
        "beginner": ["Python", "Data Structures & Algorithms", "Statistics"],
        "intermediate": ["Machine Learning", "Pandas", "NumPy", "Scikit-learn"],
        "advanced": ["Deep Learning", "TensorFlow", "PyTorch", "NLP"],
    },
    "Mobile App Developer": {
        "beginner": ["JavaScript", "Git", "Android Studio"],
        "intermediate": ["Flutter", "React Native", "REST APIs"],
        "advanced": ["Kotlin", "Swift", "Xcode"],
    },
    "UI/UX Designer": {
        "beginner": ["Wireframing", "Figma", "User Research"],
        "intermediate": ["Prototyping", "Adobe XD", "Design Systems"],
        "advanced": ["User Research", "Communication", "Teamwork"],
    },
    "DevOps Engineer": {
        "beginner": ["Linux", "Git", "Bash Scripting"],
        "intermediate": ["Docker", "AWS", "CI/CD Pipelines"],
        "advanced": ["Kubernetes", "Terraform", "Ansible"],
    },
    "Cloud Engineer": {
        "beginner": ["Linux", "Networking Fundamentals", "Git"],
        "intermediate": ["AWS", "Docker", "Bash Scripting"],
        "advanced": ["Kubernetes", "Terraform", "AWS Certified Cloud Practitioner"],
    },
    "QA / Test Engineer": {
        "beginner": ["Manual Testing", "Communication", "Problem Solving"],
        "intermediate": ["Automation Testing", "Selenium", "SQL"],
        "advanced": ["API Testing", "CI/CD Pipelines"],
    },
    "Network Engineer": {
        "beginner": ["Networking Fundamentals", "Linux"],
        "intermediate": ["Network Security", "Wireshark"],
        "advanced": ["Nmap", "CompTIA Security+"],
    },
    "Business Analyst": {
        "beginner": ["Excel", "Communication", "Problem Solving"],
        "intermediate": ["SQL", "Data Visualization", "Business Analysis"],
        "advanced": ["Statistics", "Agile/Scrum", "PMP"],
    },
    "Digital Marketing Specialist": {
        "beginner": ["Communication", "Content Writing"],
        "intermediate": ["SEO", "Social Media Marketing"],
        "advanced": ["Google Analytics", "Google Ads"],
    },

    # --- Civil Engineering ---
    "Structural Engineer": {
        "beginner": ["Engineering Mathematics", "Engineering Mechanics", "AutoCAD"],
        "intermediate": ["Structural Analysis", "Reinforced Concrete Design", "ETABS"],
        "advanced": ["Steel Structure Design", "STAAD Pro", "Earthquake Engineering"],
    },
    "Construction / Site Engineer": {
        "beginner": ["AutoCAD", "Surveying", "Engineering Mechanics"],
        "intermediate": ["Construction Management", "Estimation & Costing", "Project Planning"],
        "advanced": ["Site Supervision", "Building Codes", "Quality Control"],
    },
    "Transportation Engineer": {
        "beginner": ["Engineering Mathematics", "AutoCAD", "Surveying"],
        "intermediate": ["Transportation Engineering", "Highway Design", "Traffic Engineering"],
        "advanced": ["Civil 3D", "Geotechnical Engineering", "Project Planning"],
    },

    # --- Mechanical Engineering ---
    "Mechanical Design Engineer": {
        "beginner": ["Engineering Mathematics", "Engineering Drawing", "AutoCAD"],
        "intermediate": ["SolidWorks", "Machine Design", "Material Science"],
        "advanced": ["CATIA", "Finite Element Analysis", "ANSYS"],
    },
    "HVAC Engineer": {
        "beginner": ["Engineering Mathematics", "Thermodynamics", "AutoCAD"],
        "intermediate": ["Fluid Mechanics", "Heat Transfer", "HVAC Design"],
        "advanced": ["Revit MEP", "Energy Auditing", "Project Planning"],
    },
    "Manufacturing / Production Engineer": {
        "beginner": ["Engineering Drawing", "Material Science", "Manufacturing Processes"],
        "intermediate": ["CNC Machining", "Quality Control", "Lean Manufacturing"],
        "advanced": ["Six Sigma", "PLC Programming", "SolidWorks"],
    },

    # --- Electrical Engineering ---
    "Power Systems Engineer": {
        "beginner": ["Engineering Mathematics", "Circuit Analysis", "Electrical Machines"],
        "intermediate": ["Power Systems", "Power Electronics", "MATLAB"],
        "advanced": ["Renewable Energy Systems", "High Voltage Engineering", "SCADA"],
    },
    "Electronics Engineer": {
        "beginner": ["Circuit Analysis", "Digital Electronics", "Analog Electronics"],
        "intermediate": ["Microcontrollers", "PCB Design", "Embedded Systems"],
        "advanced": ["Signal Processing", "IoT", "MATLAB"],
    },
    "Control & Automation Engineer": {
        "beginner": ["Circuit Analysis", "Engineering Mathematics", "Electrical Machines"],
        "intermediate": ["PLC Programming", "Control Systems", "SCADA"],
        "advanced": ["Industrial Automation", "Robotics", "MATLAB"],
    },

    # --- Business & Finance ---
    "Accountant": {
        "beginner": ["Accounting", "Bookkeeping", "Excel"],
        "intermediate": ["Financial Reporting", "Taxation", "QuickBooks"],
        "advanced": ["Auditing", "Cost Accounting", "SAP"],
    },
    "Financial Analyst": {
        "beginner": ["Accounting", "Excel", "Financial Analysis"],
        "intermediate": ["Financial Modeling", "Business Analysis", "Data Visualization"],
        "advanced": ["Valuation", "Risk Management", "Statistics"],
    },
    "Human Resource (HR) Manager": {
        "beginner": ["Communication", "Human Resource Management", "Recruitment"],
        "intermediate": ["Payroll Management", "Employee Relations", "Excel"],
        "advanced": ["HR Analytics", "Organizational Development", "Leadership"],
    },
}


# ---------------------------------------------------------------------------
# Disciplines: top-level fields of study that group the roles above, so a
# student picks their broad field first (e.g. Civil Engineering) and only
# sees the roles that belong to it — instead of a flat, CS-only role list.
# ---------------------------------------------------------------------------
DISCIPLINES = {
    "Computer Science & IT": [
        "Software Engineer", "Web Developer", "Full Stack Developer", "Mobile App Developer",
        "Data Analyst", "AI Engineer", "Cybersecurity Analyst", "Network Engineer",
        "UI/UX Designer", "DevOps Engineer", "Cloud Engineer", "QA / Test Engineer",
        "Business Analyst", "Digital Marketing Specialist",
    ],
    "Civil Engineering": [
        "Structural Engineer", "Construction / Site Engineer", "Transportation Engineer",
    ],
    "Mechanical Engineering": [
        "Mechanical Design Engineer", "HVAC Engineer", "Manufacturing / Production Engineer",
    ],
    "Electrical Engineering": [
        "Power Systems Engineer", "Electronics Engineer", "Control & Automation Engineer",
    ],
    "Business & Finance": [
        "Accountant", "Financial Analyst", "Human Resource (HR) Manager",
    ],
}


def get_disciplines() -> dict:
    """Returns {discipline_name: [role, ...]} for the role picker."""
    return {name: list(roles) for name, roles in DISCIPLINES.items()}


def discipline_for_role(role: str | None) -> str | None:
    if not role:
        return None
    for name, roles in DISCIPLINES.items():
        if role in roles:
            return name
    return None


def all_required_skills(role: str) -> list[str]:
    phases = ROLES[role]
    seen = []
    for phase in ("beginner", "intermediate", "advanced"):
        for s in phases[phase]:
            if s not in seen:
                seen.append(s)
    return seen


# ---------------------------------------------------------------------------
# Learning resources per skill.
# ---------------------------------------------------------------------------
RESOURCES = {
    "HTML": {"course": "freeCodeCamp – Responsive Web Design", "youtube": "https://www.youtube.com/results?search_query=html+full+course", "practice": "https://www.frontendmentor.io/"},
    "CSS": {"course": "freeCodeCamp – CSS", "youtube": "https://www.youtube.com/results?search_query=css+full+course", "practice": "https://www.frontendmentor.io/"},
    "JavaScript": {"course": "The Odin Project – JavaScript", "youtube": "https://www.youtube.com/results?search_query=javascript+full+course", "practice": "https://leetcode.com/"},
    "TypeScript": {"course": "TypeScript Deep Dive (free book)", "youtube": "https://www.youtube.com/results?search_query=typescript+crash+course", "practice": "https://www.typescriptlang.org/play"},
    "React": {"course": "React Official Docs + Scrimba React Course", "youtube": "https://www.youtube.com/results?search_query=react+js+full+course", "practice": "https://www.frontendmentor.io/"},
    "Vue.js": {"course": "Vue Mastery – free lessons", "youtube": "https://www.youtube.com/results?search_query=vue+js+full+course", "practice": "https://vueschool.io/"},
    "Angular": {"course": "Angular official tutorial", "youtube": "https://www.youtube.com/results?search_query=angular+full+course", "practice": "https://angular.io/tutorial"},
    "Node.js": {"course": "freeCodeCamp – Node/Express", "youtube": "https://www.youtube.com/results?search_query=node+js+full+course", "practice": "https://www.hackerrank.com/domains/tutorials/10-days-of-javascript"},
    "Python": {"course": "freeCodeCamp – Python for Everybody", "youtube": "https://www.youtube.com/results?search_query=python+full+course", "practice": "https://www.hackerrank.com/domains/python"},
    "Django": {"course": "Django official tutorial", "youtube": "https://www.youtube.com/results?search_query=django+full+course", "practice": "https://www.djangoproject.com/"},
    "Flask": {"course": "Flask Mega-Tutorial (Miguel Grinberg)", "youtube": "https://www.youtube.com/results?search_query=flask+full+course", "practice": "https://flask.palletsprojects.com/"},
    "FastAPI": {"course": "FastAPI official docs tutorial", "youtube": "https://www.youtube.com/results?search_query=fastapi+full+course", "practice": "https://fastapi.tiangolo.com/tutorial/"},
    "Java": {"course": "freeCodeCamp – Java", "youtube": "https://www.youtube.com/results?search_query=java+full+course", "practice": "https://www.hackerrank.com/domains/java"},
    "Spring Boot": {"course": "Spring official guides", "youtube": "https://www.youtube.com/results?search_query=spring+boot+full+course", "practice": "https://spring.io/guides"},
    "C++": {"course": "freeCodeCamp – C++", "youtube": "https://www.youtube.com/results?search_query=c%2B%2B+full+course", "practice": "https://leetcode.com/"},
    "C#": {"course": "Microsoft Learn – C#", "youtube": "https://www.youtube.com/results?search_query=c%23+full+course", "practice": "https://learn.microsoft.com/en-us/training/dotnet/"},
    "PHP": {"course": "PHP The Right Way", "youtube": "https://www.youtube.com/results?search_query=php+full+course", "practice": "https://www.codecademy.com/learn/learn-php"},
    "SQL": {"course": "Mode – SQL Tutorial", "youtube": "https://www.youtube.com/results?search_query=sql+full+course", "practice": "https://sqlzoo.net/"},
    "MongoDB": {"course": "MongoDB University – free courses", "youtube": "https://www.youtube.com/results?search_query=mongodb+full+course", "practice": "https://learn.mongodb.com/"},
    "Git": {"course": "Git & GitHub – freeCodeCamp", "youtube": "https://www.youtube.com/results?search_query=git+and+github+full+course", "practice": "https://learngitbranching.js.org/"},
    "Docker": {"course": "Docker official get-started", "youtube": "https://www.youtube.com/results?search_query=docker+full+course", "practice": "https://www.katacoda.com/courses/docker"},
    "Kubernetes": {"course": "Kubernetes official basics", "youtube": "https://www.youtube.com/results?search_query=kubernetes+full+course", "practice": "https://kubernetes.io/docs/tutorials/"},
    "AWS": {"course": "AWS Skill Builder – free tier", "youtube": "https://www.youtube.com/results?search_query=aws+full+course", "practice": "https://aws.amazon.com/free/"},
    "Linux": {"course": "Linux Journey (free)", "youtube": "https://www.youtube.com/results?search_query=linux+full+course", "practice": "https://linuxjourney.com/"},
    "REST APIs": {"course": "REST API design – freeCodeCamp", "youtube": "https://www.youtube.com/results?search_query=rest+api+full+course", "practice": "https://reqres.in/"},
    "Data Structures & Algorithms": {"course": "NeetCode – DSA roadmap", "youtube": "https://www.youtube.com/results?search_query=data+structures+and+algorithms+full+course", "practice": "https://leetcode.com/"},
    "Machine Learning": {"course": "Andrew Ng – Machine Learning (Coursera, audit free)", "youtube": "https://www.youtube.com/results?search_query=machine+learning+full+course", "practice": "https://www.kaggle.com/learn"},
    "Deep Learning": {"course": "DeepLearning.AI – free audit", "youtube": "https://www.youtube.com/results?search_query=deep+learning+full+course", "practice": "https://www.kaggle.com/learn/intro-to-deep-learning"},
    "TensorFlow": {"course": "TensorFlow official tutorials", "youtube": "https://www.youtube.com/results?search_query=tensorflow+full+course", "practice": "https://www.tensorflow.org/tutorials"},
    "PyTorch": {"course": "PyTorch official tutorials", "youtube": "https://www.youtube.com/results?search_query=pytorch+full+course", "practice": "https://pytorch.org/tutorials/"},
    "Pandas": {"course": "Kaggle – Pandas micro-course", "youtube": "https://www.youtube.com/results?search_query=pandas+full+course", "practice": "https://www.kaggle.com/learn/pandas"},
    "NumPy": {"course": "NumPy official quickstart", "youtube": "https://www.youtube.com/results?search_query=numpy+full+course", "practice": "https://www.w3schools.com/python/numpy/"},
    "Scikit-learn": {"course": "Scikit-learn official tutorials", "youtube": "https://www.youtube.com/results?search_query=scikit+learn+full+course", "practice": "https://scikit-learn.org/stable/tutorial/"},
    "NLP": {"course": "Hugging Face NLP Course (free)", "youtube": "https://www.youtube.com/results?search_query=nlp+full+course", "practice": "https://huggingface.co/learn/nlp-course"},
    "Data Visualization": {"course": "Kaggle – Data Viz micro-course", "youtube": "https://www.youtube.com/results?search_query=data+visualization+full+course", "practice": "https://www.kaggle.com/learn/data-visualization"},
    "Statistics": {"course": "Khan Academy – Statistics", "youtube": "https://www.youtube.com/results?search_query=statistics+full+course", "practice": "https://www.khanacademy.org/math/statistics-probability"},
    "Excel": {"course": "Microsoft Excel official training", "youtube": "https://www.youtube.com/results?search_query=excel+full+course", "practice": "https://exceljet.net/"},
    "Cybersecurity Fundamentals": {"course": "Cisco Networking Academy – Intro to Cybersecurity (free)", "youtube": "https://www.youtube.com/results?search_query=cybersecurity+full+course", "practice": "https://tryhackme.com/"},
    "Network Security": {"course": "Cisco Networking Academy", "youtube": "https://www.youtube.com/results?search_query=network+security+full+course", "practice": "https://tryhackme.com/"},
    "Penetration Testing": {"course": "TryHackMe – Pentesting path", "youtube": "https://www.youtube.com/results?search_query=penetration+testing+full+course", "practice": "https://tryhackme.com/"},
    "SIEM Tools": {"course": "Splunk Fundamentals (free)", "youtube": "https://www.youtube.com/results?search_query=splunk+siem+tutorial", "practice": "https://www.splunk.com/en_us/training.html"},
    "Wireshark": {"course": "Wireshark official docs", "youtube": "https://www.youtube.com/results?search_query=wireshark+full+tutorial", "practice": "https://www.wireshark.org/docs/"},
    "Nmap": {"course": "Nmap official reference guide", "youtube": "https://www.youtube.com/results?search_query=nmap+full+tutorial", "practice": "https://tryhackme.com/room/furthernmap"},
    "Metasploit": {"course": "Metasploit Unleashed (free)", "youtube": "https://www.youtube.com/results?search_query=metasploit+full+tutorial", "practice": "https://tryhackme.com/"},
    "Cryptography": {"course": "Khan Academy – Cryptography", "youtube": "https://www.youtube.com/results?search_query=cryptography+full+course", "practice": "https://cryptohack.org/"},
    "Flutter": {"course": "Flutter official codelabs", "youtube": "https://www.youtube.com/results?search_query=flutter+full+course", "practice": "https://flutter.dev/learn"},
    "React Native": {"course": "React Native official docs", "youtube": "https://www.youtube.com/results?search_query=react+native+full+course", "practice": "https://reactnative.dev/docs/tutorial"},
    "Kotlin": {"course": "Kotlin official koans", "youtube": "https://www.youtube.com/results?search_query=kotlin+full+course", "practice": "https://play.kotlinlang.org/koans"},
    "Swift": {"course": "Swift Playgrounds (free)", "youtube": "https://www.youtube.com/results?search_query=swift+full+course", "practice": "https://www.hackingwithswift.com/"},
    "Android Studio": {"course": "Android Developers – free training", "youtube": "https://www.youtube.com/results?search_query=android+studio+full+course", "practice": "https://developer.android.com/courses"},
    "Xcode": {"course": "Apple Developer – Xcode docs", "youtube": "https://www.youtube.com/results?search_query=xcode+full+tutorial", "practice": "https://developer.apple.com/tutorials/"},
    "Figma": {"course": "Figma official Academy (free)", "youtube": "https://www.youtube.com/results?search_query=figma+full+course", "practice": "https://www.figma.com/community"},
    "Adobe XD": {"course": "Adobe XD tutorials (free)", "youtube": "https://www.youtube.com/results?search_query=adobe+xd+full+course", "practice": "https://xd.adobe.com/learn/"},
    "Wireframing": {"course": "Interaction Design Foundation – free articles", "youtube": "https://www.youtube.com/results?search_query=wireframing+tutorial", "practice": "https://www.figma.com/community"},
    "Prototyping": {"course": "Google UX Design Certificate (audit free)", "youtube": "https://www.youtube.com/results?search_query=prototyping+ux+tutorial", "practice": "https://www.figma.com/community"},
    "User Research": {"course": "Interaction Design Foundation – UX Research", "youtube": "https://www.youtube.com/results?search_query=user+research+tutorial", "practice": "https://www.nngroup.com/"},
    "Design Systems": {"course": "Design Systems Handbook (free)", "youtube": "https://www.youtube.com/results?search_query=design+systems+tutorial", "practice": "https://www.designsystems.com/"},
    "Communication": {"course": "Coursera – Effective Communication (audit free)", "youtube": "https://www.youtube.com/results?search_query=communication+skills+course", "practice": "Toastmasters local chapter"},
    "Teamwork": {"course": "LinkedIn Learning – Teamwork Foundations", "youtube": "https://www.youtube.com/results?search_query=teamwork+skills+course", "practice": "Group hackathons / open-source contributions"},
    "Problem Solving": {"course": "Coursera – Critical Thinking (audit free)", "youtube": "https://www.youtube.com/results?search_query=problem+solving+skills", "practice": "https://www.hackerrank.com/"},
    "Time Management": {"course": "Coursera – Work Smarter, Not Harder (audit free)", "youtube": "https://www.youtube.com/results?search_query=time+management+course", "practice": "Personal Kanban board (Trello)"},
    "Leadership": {"course": "Coursera – Leadership skills (audit free)", "youtube": "https://www.youtube.com/results?search_query=leadership+skills+course", "practice": "Lead a student society / open-source project"},
    "Adaptability": {"course": "LinkedIn Learning – Adaptability", "youtube": "https://www.youtube.com/results?search_query=adaptability+skills", "practice": "Cross-functional team projects"},
    "AWS Certified Cloud Practitioner": {"course": "AWS Skill Builder exam prep", "youtube": "https://www.youtube.com/results?search_query=aws+cloud+practitioner+full+course", "practice": "https://aws.amazon.com/certification/certified-cloud-practitioner/"},
    "Google Data Analytics Certificate": {"course": "Coursera – Google Data Analytics", "youtube": "https://www.youtube.com/results?search_query=google+data+analytics+certificate", "practice": "https://www.coursera.org/professional-certificates/google-data-analytics"},
    "CompTIA Security+": {"course": "Professor Messer – Security+ (free)", "youtube": "https://www.youtube.com/results?search_query=comptia+security+full+course", "practice": "https://www.professormesser.com/"},
    "PMP": {"course": "PMI – PMP exam prep", "youtube": "https://www.youtube.com/results?search_query=pmp+exam+prep+course", "practice": "https://www.pmi.org/certifications/project-management-pmp"},
    "Bash Scripting": {"course": "freeCodeCamp – Bash Scripting", "youtube": "https://www.youtube.com/results?search_query=bash+scripting+full+course", "practice": "https://www.hackerrank.com/domains/shell"},
    "CI/CD Pipelines": {"course": "GitHub Actions official docs", "youtube": "https://www.youtube.com/results?search_query=ci+cd+pipeline+tutorial", "practice": "https://docs.github.com/en/actions"},
    "Terraform": {"course": "HashiCorp Learn – Terraform (free)", "youtube": "https://www.youtube.com/results?search_query=terraform+full+course", "practice": "https://developer.hashicorp.com/terraform/tutorials"},
    "Ansible": {"course": "Ansible official docs", "youtube": "https://www.youtube.com/results?search_query=ansible+full+course", "practice": "https://www.ansible.com/resources/get-started"},
    "Networking Fundamentals": {"course": "Cisco Networking Academy – Networking Basics (free)", "youtube": "https://www.youtube.com/results?search_query=computer+networking+full+course", "practice": "https://www.geeksforgeeks.org/computer-network-tutorials/"},
    "Manual Testing": {"course": "Guru99 – Manual Testing (free)", "youtube": "https://www.youtube.com/results?search_query=manual+testing+full+course", "practice": "https://www.guru99.com/software-testing.html"},
    "Automation Testing": {"course": "Test Automation University (free)", "youtube": "https://www.youtube.com/results?search_query=automation+testing+full+course", "practice": "https://testautomationu.applitools.com/"},
    "Selenium": {"course": "Selenium official docs", "youtube": "https://www.youtube.com/results?search_query=selenium+full+course", "practice": "https://www.selenium.dev/documentation/"},
    "API Testing": {"course": "Postman Academy (free)", "youtube": "https://www.youtube.com/results?search_query=api+testing+postman+tutorial", "practice": "https://academy.postman.com/"},
    "Content Writing": {"course": "HubSpot Academy – Content Marketing (free)", "youtube": "https://www.youtube.com/results?search_query=content+writing+course", "practice": "https://www.hubspot.com/content-marketing-course"},
    "SEO": {"course": "Google – SEO Starter Guide (free)", "youtube": "https://www.youtube.com/results?search_query=seo+full+course", "practice": "https://developers.google.com/search/docs/fundamentals/seo-starter-guide"},
    "Social Media Marketing": {"course": "HubSpot Academy – Social Media (free)", "youtube": "https://www.youtube.com/results?search_query=social+media+marketing+course", "practice": "https://academy.hubspot.com/courses/social-media"},
    "Google Analytics": {"course": "Google Skillshop – Analytics (free)", "youtube": "https://www.youtube.com/results?search_query=google+analytics+full+course", "practice": "https://skillshop.withgoogle.com/"},
    "Google Ads": {"course": "Google Skillshop – Google Ads (free)", "youtube": "https://www.youtube.com/results?search_query=google+ads+full+course", "practice": "https://skillshop.withgoogle.com/"},
    "Business Analysis": {"course": "Coursera – Business Analysis Fundamentals (audit free)", "youtube": "https://www.youtube.com/results?search_query=business+analysis+course", "practice": "https://www.iiba.org/"},
    "Agile/Scrum": {"course": "Scrum.org – Learning Series (free)", "youtube": "https://www.youtube.com/results?search_query=agile+scrum+full+course", "practice": "https://www.scrum.org/resources"},

    # --- Shared engineering foundations ---
    "Engineering Mathematics": {"course": "Khan Academy – Calculus & Linear Algebra", "youtube": "https://www.youtube.com/results?search_query=engineering+mathematics+full+course", "practice": "https://www.khanacademy.org/math"},
    "Engineering Mechanics": {"course": "MIT OCW – Engineering Mechanics", "youtube": "https://www.youtube.com/results?search_query=engineering+mechanics+statics+dynamics", "practice": "https://ocw.mit.edu/"},
    "Engineering Drawing": {"course": "NPTEL – Engineering Drawing & Graphics", "youtube": "https://www.youtube.com/results?search_query=engineering+drawing+full+course", "practice": "https://nptel.ac.in/"},
    "AutoCAD": {"course": "Autodesk – AutoCAD official tutorials", "youtube": "https://www.youtube.com/results?search_query=autocad+full+course", "practice": "https://www.autodesk.com/certification/all-certifications/autocad-certified-user"},
    "Project Planning": {"course": "Oracle Primavera P6 – tutorials", "youtube": "https://www.youtube.com/results?search_query=primavera+p6+full+course", "practice": "https://www.coursera.org/courses?query=project%20management"},
    "Quality Control": {"course": "ASQ – Quality Basics (free resources)", "youtube": "https://www.youtube.com/results?search_query=quality+control+engineering+course", "practice": "https://asq.org/quality-resources"},

    # --- Civil Engineering ---
    "Structural Analysis": {"course": "NPTEL – Structural Analysis", "youtube": "https://www.youtube.com/results?search_query=structural+analysis+full+course", "practice": "https://nptel.ac.in/courses/105105166"},
    "Reinforced Concrete Design": {"course": "NPTEL – Reinforced Concrete Design", "youtube": "https://www.youtube.com/results?search_query=reinforced+concrete+design+course", "practice": "https://nptel.ac.in/"},
    "Steel Structure Design": {"course": "NPTEL – Design of Steel Structures", "youtube": "https://www.youtube.com/results?search_query=design+of+steel+structures+course", "practice": "https://nptel.ac.in/"},
    "ETABS": {"course": "CSI ETABS – official watch & learn", "youtube": "https://www.youtube.com/results?search_query=etabs+full+tutorial", "practice": "https://www.csiamerica.com/products/etabs/watch-and-learn"},
    "STAAD Pro": {"course": "Bentley STAAD.Pro tutorials", "youtube": "https://www.youtube.com/results?search_query=staad+pro+full+tutorial", "practice": "https://learn.bentley.com/"},
    "Civil 3D": {"course": "Autodesk Civil 3D tutorials", "youtube": "https://www.youtube.com/results?search_query=civil+3d+full+course", "practice": "https://www.autodesk.com/support/technical/product/civil-3d"},
    "Earthquake Engineering": {"course": "NPTEL – Earthquake Engineering", "youtube": "https://www.youtube.com/results?search_query=earthquake+engineering+course", "practice": "https://nptel.ac.in/"},
    "Surveying": {"course": "NPTEL – Surveying", "youtube": "https://www.youtube.com/results?search_query=surveying+civil+engineering+course", "practice": "https://nptel.ac.in/"},
    "Construction Management": {"course": "Coursera – Construction Management (audit free)", "youtube": "https://www.youtube.com/results?search_query=construction+management+course", "practice": "https://www.coursera.org/specializations/construction-management"},
    "Estimation & Costing": {"course": "NPTEL – Estimation & Costing", "youtube": "https://www.youtube.com/results?search_query=estimation+and+costing+civil+course", "practice": "https://nptel.ac.in/"},
    "Site Supervision": {"course": "Construction site supervision guides", "youtube": "https://www.youtube.com/results?search_query=construction+site+supervision", "practice": "https://www.coursera.org/courses?query=construction"},
    "Building Codes": {"course": "Building Code of Pakistan / ACI overview", "youtube": "https://www.youtube.com/results?search_query=building+codes+civil+engineering", "practice": "https://www.pec.org.pk/"},
    "Transportation Engineering": {"course": "NPTEL – Transportation Engineering", "youtube": "https://www.youtube.com/results?search_query=transportation+engineering+course", "practice": "https://nptel.ac.in/"},
    "Highway Design": {"course": "NPTEL – Highway Engineering", "youtube": "https://www.youtube.com/results?search_query=highway+design+engineering+course", "practice": "https://nptel.ac.in/"},
    "Traffic Engineering": {"course": "NPTEL – Traffic Engineering", "youtube": "https://www.youtube.com/results?search_query=traffic+engineering+course", "practice": "https://nptel.ac.in/"},
    "Geotechnical Engineering": {"course": "NPTEL – Geotechnical Engineering", "youtube": "https://www.youtube.com/results?search_query=geotechnical+engineering+course", "practice": "https://nptel.ac.in/"},

    # --- Mechanical Engineering ---
    "SolidWorks": {"course": "SolidWorks official tutorials", "youtube": "https://www.youtube.com/results?search_query=solidworks+full+course", "practice": "https://www.solidworks.com/support/certification"},
    "CATIA": {"course": "CATIA V5 tutorials", "youtube": "https://www.youtube.com/results?search_query=catia+v5+full+course", "practice": "https://www.3ds.com/edu/education/students"},
    "ANSYS": {"course": "ANSYS Innovation Courses (free)", "youtube": "https://www.youtube.com/results?search_query=ansys+full+tutorial", "practice": "https://courses.ansys.com/"},
    "Machine Design": {"course": "NPTEL – Machine Design", "youtube": "https://www.youtube.com/results?search_query=machine+design+full+course", "practice": "https://nptel.ac.in/"},
    "Material Science": {"course": "MIT OCW – Materials Science", "youtube": "https://www.youtube.com/results?search_query=material+science+engineering+course", "practice": "https://ocw.mit.edu/"},
    "Finite Element Analysis": {"course": "NPTEL – Finite Element Method", "youtube": "https://www.youtube.com/results?search_query=finite+element+analysis+course", "practice": "https://nptel.ac.in/"},
    "Thermodynamics": {"course": "MIT OCW – Thermodynamics", "youtube": "https://www.youtube.com/results?search_query=thermodynamics+full+course", "practice": "https://ocw.mit.edu/"},
    "Fluid Mechanics": {"course": "NPTEL – Fluid Mechanics", "youtube": "https://www.youtube.com/results?search_query=fluid+mechanics+full+course", "practice": "https://nptel.ac.in/"},
    "Heat Transfer": {"course": "NPTEL – Heat Transfer", "youtube": "https://www.youtube.com/results?search_query=heat+transfer+full+course", "practice": "https://nptel.ac.in/"},
    "HVAC Design": {"course": "ASHRAE – HVAC fundamentals", "youtube": "https://www.youtube.com/results?search_query=hvac+design+full+course", "practice": "https://www.ashrae.org/professional-development"},
    "Revit MEP": {"course": "Autodesk Revit MEP tutorials", "youtube": "https://www.youtube.com/results?search_query=revit+mep+full+course", "practice": "https://www.autodesk.com/support/technical/product/revit-products"},
    "Energy Auditing": {"course": "Energy auditing fundamentals", "youtube": "https://www.youtube.com/results?search_query=energy+audit+course", "practice": "https://www.coursera.org/courses?query=energy%20efficiency"},
    "Manufacturing Processes": {"course": "NPTEL – Manufacturing Processes", "youtube": "https://www.youtube.com/results?search_query=manufacturing+processes+course", "practice": "https://nptel.ac.in/"},
    "CNC Machining": {"course": "CNC machining fundamentals", "youtube": "https://www.youtube.com/results?search_query=cnc+machining+full+course", "practice": "https://academy.titansofcnc.com/"},
    "Lean Manufacturing": {"course": "Coursera – Lean Production (audit free)", "youtube": "https://www.youtube.com/results?search_query=lean+manufacturing+course", "practice": "https://www.coursera.org/courses?query=lean"},
    "Six Sigma": {"course": "Council for Six Sigma – free Green Belt material", "youtube": "https://www.youtube.com/results?search_query=six+sigma+green+belt+full+course", "practice": "https://www.sixsigmacouncil.org/"},

    # --- Electrical Engineering ---
    "Circuit Analysis": {"course": "MIT OCW – Circuits & Electronics", "youtube": "https://www.youtube.com/results?search_query=circuit+analysis+full+course", "practice": "https://ocw.mit.edu/"},
    "Electrical Machines": {"course": "NPTEL – Electrical Machines", "youtube": "https://www.youtube.com/results?search_query=electrical+machines+full+course", "practice": "https://nptel.ac.in/"},
    "Power Systems": {"course": "NPTEL – Power Systems", "youtube": "https://www.youtube.com/results?search_query=power+system+analysis+full+course", "practice": "https://nptel.ac.in/"},
    "Power Electronics": {"course": "NPTEL – Power Electronics", "youtube": "https://www.youtube.com/results?search_query=power+electronics+full+course", "practice": "https://nptel.ac.in/"},
    "MATLAB": {"course": "MATLAB Onramp (free, official)", "youtube": "https://www.youtube.com/results?search_query=matlab+full+course", "practice": "https://matlabacademy.mathworks.com/"},
    "Renewable Energy Systems": {"course": "Coursera – Solar Energy (audit free)", "youtube": "https://www.youtube.com/results?search_query=renewable+energy+systems+course", "practice": "https://www.coursera.org/courses?query=renewable%20energy"},
    "High Voltage Engineering": {"course": "NPTEL – High Voltage Engineering", "youtube": "https://www.youtube.com/results?search_query=high+voltage+engineering+course", "practice": "https://nptel.ac.in/"},
    "SCADA": {"course": "SCADA systems fundamentals", "youtube": "https://www.youtube.com/results?search_query=scada+full+tutorial", "practice": "https://www.udemy.com/topic/scada/"},
    "Digital Electronics": {"course": "NPTEL – Digital Electronics", "youtube": "https://www.youtube.com/results?search_query=digital+electronics+full+course", "practice": "https://nptel.ac.in/"},
    "Analog Electronics": {"course": "NPTEL – Analog Electronics", "youtube": "https://www.youtube.com/results?search_query=analog+electronics+full+course", "practice": "https://nptel.ac.in/"},
    "Microcontrollers": {"course": "Arduino official – Getting Started", "youtube": "https://www.youtube.com/results?search_query=microcontroller+arduino+full+course", "practice": "https://www.arduino.cc/en/Guide"},
    "PCB Design": {"course": "Altium / KiCad tutorials", "youtube": "https://www.youtube.com/results?search_query=pcb+design+full+course", "practice": "https://www.kicad.org/"},
    "Embedded Systems": {"course": "NPTEL – Embedded Systems", "youtube": "https://www.youtube.com/results?search_query=embedded+systems+full+course", "practice": "https://www.edx.org/learn/embedded-systems"},
    "Signal Processing": {"course": "MIT OCW – Signals & Systems", "youtube": "https://www.youtube.com/results?search_query=digital+signal+processing+course", "practice": "https://ocw.mit.edu/"},
    "IoT": {"course": "Coursera – Intro to IoT (audit free)", "youtube": "https://www.youtube.com/results?search_query=iot+full+course", "practice": "https://www.netacad.com/courses/iot"},
    "PLC Programming": {"course": "PLC programming fundamentals", "youtube": "https://www.youtube.com/results?search_query=plc+programming+full+course", "practice": "https://www.udemy.com/topic/plc-programming/"},
    "Control Systems": {"course": "NPTEL – Control Systems", "youtube": "https://www.youtube.com/results?search_query=control+systems+engineering+course", "practice": "https://nptel.ac.in/"},
    "Industrial Automation": {"course": "Industrial automation fundamentals", "youtube": "https://www.youtube.com/results?search_query=industrial+automation+course", "practice": "https://www.udemy.com/topic/industrial-automation/"},
    "Robotics": {"course": "Coursera – Robotics (audit free)", "youtube": "https://www.youtube.com/results?search_query=robotics+full+course", "practice": "https://www.coursera.org/specializations/robotics"},

    # --- Business & Finance ---
    "Accounting": {"course": "ACCA / edX – Intro to Accounting", "youtube": "https://www.youtube.com/results?search_query=accounting+full+course", "practice": "https://www.edx.org/learn/accounting"},
    "Bookkeeping": {"course": "Intuit Bookkeeping (Coursera, audit free)", "youtube": "https://www.youtube.com/results?search_query=bookkeeping+full+course", "practice": "https://www.coursera.org/professional-certificates/intuit-bookkeeping"},
    "Financial Reporting": {"course": "edX – Financial Reporting", "youtube": "https://www.youtube.com/results?search_query=financial+reporting+course", "practice": "https://www.edx.org/learn/financial-reporting"},
    "Taxation": {"course": "FBR / taxation basics", "youtube": "https://www.youtube.com/results?search_query=taxation+basics+course", "practice": "https://www.fbr.gov.pk/"},
    "QuickBooks": {"course": "QuickBooks official tutorials", "youtube": "https://www.youtube.com/results?search_query=quickbooks+full+course", "practice": "https://quickbooks.intuit.com/tutorials/"},
    "Auditing": {"course": "ACCA – Audit & Assurance material", "youtube": "https://www.youtube.com/results?search_query=auditing+full+course", "practice": "https://www.accaglobal.com/"},
    "Cost Accounting": {"course": "Cost accounting fundamentals", "youtube": "https://www.youtube.com/results?search_query=cost+accounting+full+course", "practice": "https://www.edx.org/learn/accounting"},
    "SAP": {"course": "SAP Learning Hub (free tier)", "youtube": "https://www.youtube.com/results?search_query=sap+erp+full+course", "practice": "https://learning.sap.com/"},
    "Financial Analysis": {"course": "CFI – Financial Analysis Fundamentals", "youtube": "https://www.youtube.com/results?search_query=financial+analysis+full+course", "practice": "https://corporatefinanceinstitute.com/"},
    "Financial Modeling": {"course": "CFI – Financial Modeling (FMVA)", "youtube": "https://www.youtube.com/results?search_query=financial+modeling+full+course", "practice": "https://corporatefinanceinstitute.com/"},
    "Valuation": {"course": "NYU Stern – Aswath Damodaran (free)", "youtube": "https://www.youtube.com/results?search_query=valuation+dcf+course", "practice": "https://pages.stern.nyu.edu/~adamodar/"},
    "Risk Management": {"course": "Coursera – Financial Risk Management (audit free)", "youtube": "https://www.youtube.com/results?search_query=financial+risk+management+course", "practice": "https://www.coursera.org/courses?query=risk%20management"},
    "Human Resource Management": {"course": "Coursera – HR Management (audit free)", "youtube": "https://www.youtube.com/results?search_query=human+resource+management+course", "practice": "https://www.coursera.org/specializations/human-resource-management"},
    "Recruitment": {"course": "LinkedIn Learning – Recruiting Foundations", "youtube": "https://www.youtube.com/results?search_query=recruitment+talent+acquisition+course", "practice": "https://www.coursera.org/courses?query=recruitment"},
    "Payroll Management": {"course": "Payroll fundamentals", "youtube": "https://www.youtube.com/results?search_query=payroll+management+course", "practice": "https://www.coursera.org/courses?query=payroll"},
    "Employee Relations": {"course": "SHRM – Employee Relations resources", "youtube": "https://www.youtube.com/results?search_query=employee+relations+course", "practice": "https://www.shrm.org/"},
    "HR Analytics": {"course": "Coursera – People Analytics (audit free)", "youtube": "https://www.youtube.com/results?search_query=hr+analytics+course", "practice": "https://www.coursera.org/learn/wharton-people-analytics"},
    "Organizational Development": {"course": "Organizational development fundamentals", "youtube": "https://www.youtube.com/results?search_query=organizational+development+course", "practice": "https://www.coursera.org/courses?query=organizational%20development"},
}

DEFAULT_RESOURCE = {"course": "Search Coursera / edX for a free-audit course", "youtube": "https://www.youtube.com/", "practice": "https://www.google.com/search?q=practice+platform"}

# ---------------------------------------------------------------------------
# Broad career fields, used to keep the Opportunity Finder relevant to the
# candidate's target role (e.g. a Cybersecurity Analyst shouldn't be shown
# Web Development listings just because of a small skill overlap).
# ---------------------------------------------------------------------------
ROLE_FIELDS = {
    "Software Engineer": "Software Development",
    "Web Developer": "Software Development",
    "Full Stack Developer": "Software Development",
    "Mobile App Developer": "Software Development",
    "Data Analyst": "Data & AI",
    "AI Engineer": "Data & AI",
    "Cybersecurity Analyst": "Cybersecurity & Networking",
    "Network Engineer": "Cybersecurity & Networking",
    "UI/UX Designer": "Design",
    "DevOps Engineer": "Cloud & DevOps",
    "Cloud Engineer": "Cloud & DevOps",
    "QA / Test Engineer": "QA & Testing",
    "Business Analyst": "Business & Marketing",
    "Digital Marketing Specialist": "Business & Marketing",
    # Civil
    "Structural Engineer": "Civil Engineering",
    "Construction / Site Engineer": "Civil Engineering",
    "Transportation Engineer": "Civil Engineering",
    # Mechanical
    "Mechanical Design Engineer": "Mechanical Engineering",
    "HVAC Engineer": "Mechanical Engineering",
    "Manufacturing / Production Engineer": "Mechanical Engineering",
    # Electrical
    "Power Systems Engineer": "Electrical Engineering",
    "Electronics Engineer": "Electrical Engineering",
    "Control & Automation Engineer": "Electrical Engineering",
    # Business & Finance
    "Accountant": "Finance & Accounting",
    "Financial Analyst": "Finance & Accounting",
    "Human Resource (HR) Manager": "Human Resources",
}


def get_fields() -> list[str]:
    seen = []
    for field in ROLE_FIELDS.values():
        if field not in seen:
            seen.append(field)
    return seen


def field_for_role(role: str | None) -> str | None:
    return ROLE_FIELDS.get(role) if role else None


# ---------------------------------------------------------------------------
# Sample Pakistani-market opportunities (curated static demo data).
# ---------------------------------------------------------------------------
OPPORTUNITIES = [
    {"title": "Junior Web Developer", "company": "Techlogix", "location": "Lahore", "type": "Job", "field": "Software Development", "skills": ["HTML", "CSS", "JavaScript", "React"]},
    {"title": "Full Stack Developer Intern", "company": "Systems Limited", "location": "Lahore", "type": "Internship", "field": "Software Development", "skills": ["React", "Node.js", "MongoDB", "Git"]},
    {"title": "Data Analyst", "company": "NetSol Technologies", "location": "Lahore", "type": "Job", "field": "Data & AI", "skills": ["SQL", "Excel", "Python", "Pandas", "Data Visualization"]},
    {"title": "Remote Frontend Developer", "company": "Arbisoft", "location": "Remote", "type": "Remote", "field": "Software Development", "skills": ["HTML", "CSS", "JavaScript", "React"]},
    {"title": "AI/ML Intern", "company": "Afiniti", "location": "Karachi", "type": "Internship", "field": "Data & AI", "skills": ["Python", "Machine Learning", "Pandas", "NumPy"]},
    {"title": "Cybersecurity Analyst", "company": "TPS Pakistan", "location": "Karachi", "type": "Job", "field": "Cybersecurity & Networking", "skills": ["Cybersecurity Fundamentals", "Network Security", "Wireshark", "SIEM Tools"]},
    {"title": "SOC Analyst Intern", "company": "Ufone", "location": "Islamabad", "type": "Internship", "field": "Cybersecurity & Networking", "skills": ["Cybersecurity Fundamentals", "SIEM Tools", "Network Security"]},
    {"title": "Network Security Engineer", "company": "PTCL", "location": "Islamabad", "type": "Job", "field": "Cybersecurity & Networking", "skills": ["Networking Fundamentals", "Network Security", "Linux"]},
    {"title": "Mobile App Developer", "company": "10Pearls", "location": "Lahore", "type": "Job", "field": "Software Development", "skills": ["Flutter", "REST APIs", "Git"]},
    {"title": "UI/UX Design Intern", "company": "Folio3", "location": "Karachi", "type": "Internship", "field": "Design", "skills": ["Figma", "Wireframing", "Prototyping"]},
    {"title": "Freelance React Developer", "company": "Upwork Client (PK)", "location": "Remote", "type": "Freelance", "field": "Software Development", "skills": ["React", "JavaScript", "REST APIs"]},
    {"title": "Backend Developer (Python)", "company": "Careem", "location": "Islamabad", "type": "Job", "field": "Software Development", "skills": ["Python", "Django", "SQL", "Docker"]},
    {"title": "Data Science Intern", "company": "Bykea", "location": "Karachi", "type": "Internship", "field": "Data & AI", "skills": ["Python", "Machine Learning", "Statistics", "SQL"]},
    {"title": "Penetration Tester", "company": "Rewterz", "location": "Karachi", "type": "Job", "field": "Cybersecurity & Networking", "skills": ["Penetration Testing", "Nmap", "Metasploit", "Linux"]},
    {"title": "Remote DevOps Engineer", "company": "Contour Software", "location": "Remote", "type": "Remote", "field": "Cloud & DevOps", "skills": ["Docker", "Kubernetes", "AWS", "Linux"]},
    {"title": "Cloud Support Intern", "company": "Systems Limited", "location": "Lahore", "type": "Internship", "field": "Cloud & DevOps", "skills": ["AWS", "Linux", "Networking Fundamentals"]},
    {"title": "Freelance UI/UX Designer", "company": "Fiverr Client (PK)", "location": "Remote", "type": "Freelance", "field": "Design", "skills": ["Figma", "Adobe XD", "Prototyping"]},
    {"title": "Software Engineer", "company": "Devsinc", "location": "Lahore", "type": "Job", "field": "Software Development", "skills": ["Java", "Spring Boot", "SQL", "Git"]},
    {"title": "QA Automation Engineer", "company": "Systems Limited", "location": "Lahore", "type": "Job", "field": "QA & Testing", "skills": ["Automation Testing", "Selenium", "SQL"]},
    {"title": "Manual QA Intern", "company": "10Pearls", "location": "Karachi", "type": "Internship", "field": "QA & Testing", "skills": ["Manual Testing", "Communication", "Problem Solving"]},
    {"title": "Digital Marketing Executive", "company": "Daraz", "location": "Lahore", "type": "Job", "field": "Business & Marketing", "skills": ["SEO", "Social Media Marketing", "Google Analytics"]},
    {"title": "Business Analyst Intern", "company": "Jazz", "location": "Islamabad", "type": "Internship", "field": "Business & Marketing", "skills": ["Excel", "Communication", "Business Analysis"]},

    # --- Civil Engineering ---
    {"title": "Site Engineer", "company": "Habib Construction Services", "location": "Lahore", "type": "Job", "field": "Civil Engineering", "skills": ["AutoCAD", "Construction Management", "Site Supervision", "Estimation & Costing"]},
    {"title": "Structural Design Intern", "company": "NESPAK", "location": "Lahore", "type": "Internship", "field": "Civil Engineering", "skills": ["AutoCAD", "Structural Analysis", "ETABS"]},
    {"title": "Junior Civil Engineer", "company": "Frontier Works Organization (FWO)", "location": "Islamabad", "type": "Job", "field": "Civil Engineering", "skills": ["Surveying", "AutoCAD", "Project Planning"]},

    # --- Mechanical Engineering ---
    {"title": "Mechanical Design Engineer", "company": "Millat Tractors", "location": "Lahore", "type": "Job", "field": "Mechanical Engineering", "skills": ["SolidWorks", "Machine Design", "AutoCAD"]},
    {"title": "HVAC Engineer", "company": "Pak Elektron (PEL)", "location": "Lahore", "type": "Job", "field": "Mechanical Engineering", "skills": ["HVAC Design", "Thermodynamics", "AutoCAD"]},
    {"title": "Production Engineer Intern", "company": "Atlas Honda", "location": "Karachi", "type": "Internship", "field": "Mechanical Engineering", "skills": ["Manufacturing Processes", "Quality Control", "Material Science"]},

    # --- Electrical Engineering ---
    {"title": "Electrical Engineer", "company": "K-Electric", "location": "Karachi", "type": "Job", "field": "Electrical Engineering", "skills": ["Power Systems", "Electrical Machines", "Circuit Analysis"]},
    {"title": "Automation Engineer", "company": "Siemens Pakistan", "location": "Islamabad", "type": "Job", "field": "Electrical Engineering", "skills": ["PLC Programming", "SCADA", "Control Systems"]},
    {"title": "Electronics Design Intern", "company": "NRTC", "location": "Haripur", "type": "Internship", "field": "Electrical Engineering", "skills": ["PCB Design", "Microcontrollers", "Embedded Systems"]},

    # --- Finance & Accounting / HR ---
    {"title": "Junior Accountant", "company": "A.F. Ferguson & Co. (PwC)", "location": "Karachi", "type": "Job", "field": "Finance & Accounting", "skills": ["Accounting", "Bookkeeping", "Excel", "Taxation"]},
    {"title": "Financial Analyst", "company": "Habib Bank Limited (HBL)", "location": "Karachi", "type": "Job", "field": "Finance & Accounting", "skills": ["Financial Analysis", "Financial Modeling", "Excel"]},
    {"title": "HR Intern", "company": "Nestlé Pakistan", "location": "Lahore", "type": "Internship", "field": "Human Resources", "skills": ["Human Resource Management", "Recruitment", "Communication"]},
]


def get_role_names() -> list[str]:
    return list(ROLES.keys())


def is_valid_role(role: str | None) -> bool:
    return role in ROLES


# ---------------------------------------------------------------------------
# Recommended certifications per role (shown in analysis/roadmap + advisor).
# ---------------------------------------------------------------------------
ROLE_CERTIFICATIONS = {
    "Software Engineer": ["AWS Certified Cloud Practitioner"],
    "Web Developer": ["AWS Certified Cloud Practitioner"],
    "Full Stack Developer": ["AWS Certified Cloud Practitioner"],
    "Data Analyst": ["Google Data Analytics Certificate"],
    "Cybersecurity Analyst": ["CompTIA Security+"],
    "AI Engineer": ["Google Data Analytics Certificate"],
    "Mobile App Developer": ["AWS Certified Cloud Practitioner"],
    "UI/UX Designer": ["PMP"],
    "DevOps Engineer": ["AWS Certified Cloud Practitioner"],
    "Cloud Engineer": ["AWS Certified Cloud Practitioner"],
    "QA / Test Engineer": ["CompTIA Security+"],
    "Network Engineer": ["CompTIA Security+"],
    "Business Analyst": ["PMP", "Google Data Analytics Certificate"],
    "Digital Marketing Specialist": ["Google Data Analytics Certificate"],
    # Civil
    "Structural Engineer": ["PEC (Pakistan Engineering Council) Registration", "Autodesk AutoCAD Certified"],
    "Construction / Site Engineer": ["PMP", "Primavera P6 Certification"],
    "Transportation Engineer": ["PEC (Pakistan Engineering Council) Registration"],
    # Mechanical
    "Mechanical Design Engineer": ["SolidWorks Certified Associate (CSWA)", "Autodesk AutoCAD Certified"],
    "HVAC Engineer": ["ASHRAE HVAC Design Certification"],
    "Manufacturing / Production Engineer": ["Six Sigma Green Belt", "Lean Manufacturing Certificate"],
    # Electrical
    "Power Systems Engineer": ["PEC (Pakistan Engineering Council) Registration"],
    "Electronics Engineer": ["Certified IoT Specialist"],
    "Control & Automation Engineer": ["Siemens PLC / TIA Portal Certification"],
    # Business & Finance
    "Accountant": ["ACCA", "CA (Chartered Accountant)"],
    "Financial Analyst": ["CFA (Chartered Financial Analyst)", "Financial Modeling & Valuation Analyst (FMVA)"],
    "Human Resource (HR) Manager": ["SHRM-CP", "CIPD Certification"],
}
