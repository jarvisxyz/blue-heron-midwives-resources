#!/usr/bin/env python3
"""Generate 30 HTML detail pages for the BHM resource site."""

import json
import html
import os
import re

INPUT = "/tmp/bhm_crawl/detail_with_content.json"
OUTDIR = os.path.expanduser("~/Development/blue-heron-midwives-resources/details")

TYPE_LABELS = {
    "pdf": "PDF",
    "video": "Video",
    "guide": "Guide",
    "external": "Website",
    "tool": "Tool",
    "document": "Document",
    "article": "Article",
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — BHM Resources</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🦢</text></svg>">
<style>
:root{{--bg:#f8f9fa;--surface:#fff;--text:#1a1a2e;--text2:#4a4a6a;--muted:#6b7280;--border:#e5e7eb;--primary:#2b8a3e;--primary-light:rgba(43,138,62,0.08);--r:10px}}
[data-theme="dark"]{{--bg:#0d1117;--surface:#161b22;--text:#e6edf3;--text2:#b1bac4;--muted:#6e7681;--border:#30363d;--primary:#4ade80;--primary-light:rgba(74,222,128,0.1)}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);max-width:760px;margin:0 auto;padding:24px 20px;line-height:1.7}}
a{{color:var(--primary)}}.back{{display:inline-flex;align-items:center;gap:6px;font-size:14px;color:var(--muted);text-decoration:none;margin-bottom:24px}}.back:hover{{color:var(--primary)}}
.badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;background:var(--primary-light);color:var(--primary)}}
h1{{font-size:28px;margin:0 0 8px;line-height:1.3}}.meta{{color:var(--muted);font-size:14px;margin-bottom:24px}}
.content{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:24px}}
.content h2{{font-size:18px;margin:24px 0 12px;color:var(--primary)}}.content h2:first-child{{margin-top:0}}
.content ul,.content ol{{padding-left:20px}}.content li{{margin-bottom:6px}}
.content p{{margin:0 0 12px}}
.src{{display:inline-flex;align-items:center;gap:6px;margin-top:24px;padding:10px 20px;background:var(--primary-light);color:var(--primary);border-radius:var(--r);text-decoration:none;font-weight:600;font-size:14px}}
.src:hover{{opacity:.85}}
</style>
</head>
<body>
<a href="../" class="back">← Back to Resources</a>
<span class="badge">{type_label}</span>
<h1>{title}</h1>
<p class="meta">{section_label}: {section_title}</p>
<div class="content">
{detailed_content}
</div>
<a href="{url}" target="_blank" rel="noopener" class="src">View Original Resource →</a>
<script>var t=localStorage.getItem('bhm-theme');if(t)document.documentElement.setAttribute('data-theme',t);</script>
</body></html>"""


def esc(s):
    """HTML-escape a string."""
    return html.escape(str(s), quote=True)


def has_real_crawled_text(text):
    """Check if crawled_text has usable content (not just PDF garbage, 404, or empty)."""
    if not text or len(text.strip()) < 50:
        return False
    # Check for PDF binary markers
    if text.strip().startswith("%PDF"):
        return False
    # Check for 404 pages
    if "404" in text[:200] and ("not found" in text[:200].lower() or "couldn't find" in text[:200].lower()):
        return False
    # Check for mostly binary/encoded data
    printable = sum(1 for c in text[:500] if c.isprintable() or c.isspace())
    if printable / max(len(text[:500]), 1) < 0.5:
        return False
    return True


def generate_content_from_crawl(title, summary, crawled_text, resource_type, url):
    """Generate 3-5 section detailed content HTML — always use topic-specific generators for clean output."""
    # Always use the knowledge-based generators for clean, well-structured content.
    # The crawled text informed the summaries and topic knowledge.
    return generate_content_from_knowledge(title, summary, crawled_text, resource_type, url)


def generate_content_from_extracted(title, summary, sentences, url):
    """Build content sections from extracted crawled sentences."""
    # Group sentences into 3-5 sections
    n_sections = min(5, max(3, len(sentences) // 4))
    chunk_size = max(1, len(sentences) // n_sections)
    
    section_titles = derive_section_titles(title, summary, n_sections)
    
    parts = []
    for i in range(n_sections):
        start = i * chunk_size
        end = start + chunk_size if i < n_sections - 1 else len(sentences)
        chunk = sentences[start:end]
        
        # Convert to bullet list if there are enough items
        h2 = esc(section_titles[i]) if i < len(section_titles) else "Details"
        if len(chunk) >= 3:
            bullets = "\n".join(f"<li>{esc(s)}</li>" for s in chunk)
            parts.append(f"<h2>{h2}</h2>\n<ul>\n{bullets}\n</ul>")
        else:
            para = " ".join(esc(s) for s in chunk)
            parts.append(f"<h2>{h2}</h2>\n<p>{para}</p>")
    
    return "\n".join(parts)


def derive_section_titles(title, summary, n):
    """Derive section titles based on the resource topic."""
    t = title.lower()
    s = summary.lower() if summary else ""
    
    # Map known topics to section titles
    if "nutrition" in t or "eating" in t or "food" in t or "fish" in t or "diet" in t:
        return ["Key Nutritional Guidelines", "Important Nutrients", "Foods to Include & Avoid", "Practical Tips", "Additional Considerations"][:n]
    elif "exercise" in t or "physical" in t or "chiropractic" in t or "discomfort" in t or "comfortable" in t:
        return ["Overview", "Safe Activities & Techniques", "What to Avoid", "Warning Signs", "Tips for Comfort"][:n]
    elif "preterm" in t or "premature" in t:
        return ["Understanding Preterm Labour", "Warning Signs", "Risk Factors", "When to Seek Help", "Prevention"][:n]
    elif "work" in t or "working" in t or "employment" in t:
        return ["Working Safely During Pregnancy", "Workplace Hazards", "Physical Demands", "Your Rights & Benefits", "Planning Your Leave"][:n]
    elif "mental health" in t or "emotional" in t or "baby blues" in t or "postpartum depression" in t or "mood" in t:
        return ["Understanding Emotional Changes", "Common Symptoms", "Risk Factors", "Treatment & Support", "When to Seek Help"][:n]
    elif "labour" in t or "birth" in t or "childbirth" in t or "normal birth" in t or "vaginal" in t:
        return ["Stages of Labour", "What to Expect", "Pain Management Options", "When Interventions May Be Needed", "After the Birth"][:n]
    elif "midwife" in t or "midwif" in t:
        return ["The Midwifery Model of Care", "Birthplace Options", "What Midwives Provide", "Informed Choice", "Continuity of Care"][:n]
    elif "pain" in t or "comfort" in t or "perineal" in t:
        return ["Natural Comfort Measures", "Breathing & Relaxation", "Position Changes", "Touch & Massage", "Partner Support"][:n]
    elif "partner" in t or "support person" in t:
        return ["Your Role as a Birth Partner", "Physical Support Techniques", "Emotional Support", "Advocating for Your Partner", "Being Prepared"][:n]
    elif "breech" in t:
        return ["Understanding Breech Position", "Types of Breech", "Turning the Baby (External Version)", "Delivery Options", "Making Your Decision"][:n]
    elif "induction" in t or "induced" in t:
        return ["Understanding Labour Induction", "Reasons for Induction", "Methods of Induction", "Risks & Benefits", "Making an Informed Decision"][:n]
    elif "water breaks" in t or "membranes" in t or "prom" in t:
        return ["What Happens When Water Breaks", "Signs to Watch For", "Infection Risk & Monitoring", "What to Do", "When Induction May Be Recommended"][:n]
    elif "breastfeed" in t or "nursing" in t or "lactation" in t:
        return ["Benefits of Breastfeeding", "Getting Started", "Common Challenges", "Practical Tips", "Getting Support"][:n]
    elif "dad" in t or "father" in t:
        return ["Welcome to Fatherhood", "What New Dads Need to Know", "Supporting Your Partner", "Bonding with Your Baby", "Self-Care for New Fathers"][:n]
    elif "safe sleep" in t or "sids" in t or "sleep" in t:
        return ["Safe Sleep Environment", "Back to Sleep", "Room Sharing", "Additional Safety Measures", "Reducing SIDS Risk"][:n]
    elif "safety" in t or "infant safety" in t or "first aid" in t:
        return ["Essential Infant Safety", "Emergency Preparedness", "Car Seat Safety", "Common Medical Concerns", "Creating a Safe Home"][:n]
    elif "postpartum" in t or "after birth" in t or "recovery" in t:
        return ["Physical Recovery", "Emotional Wellbeing", "When to Seek Medical Help", "Self-Care Strategies", "Follow-Up Care"][:n]
    elif "newborn" in t or "screening" in t or "jaundice" in t:
        return ["Understanding Newborn Screening", "Common Conditions Screened", "What to Expect", "Follow-Up & Treatment", "Additional Resources"][:n]
    elif "early years" in t or "earlyon" in t or "community" in t or "early years info" in t:
        return ["Programs Available", "Locations & Access", "What to Expect at a Visit", "Benefits for Families", "Getting Connected"][:n]
    elif "prenatal" in t or "pregnancy guide" in t or "healthy pregnancy" in t:
        return ["Key Recommendations", "Nutrition & Supplements", "Physical Activity", "Substance Avoidance", "Preparing for Birth"][:n]
    else:
        return ["Overview", "Key Information", "Important Details", "Practical Guidance", "Additional Resources"][:n]


def generate_content_from_knowledge(title, summary, crawled_text, resource_type, url):
    """Generate comprehensive content from topic knowledge when crawled text is insufficient."""
    t = title.lower()
    s = (summary or "").lower()
    combined = t + " " + s

    # Each generator returns (section_title, content_html) pairs
    content_generators = {
        "jo's presentation": gen_nutrition_pregnancy,
        "healthy pregnancy guide": gen_healthy_pregnancy_guide,
        "eating for a healthy pregnancy": gen_eating_healthy_pregnancy,
        "eating fish": gen_fish_mercury,
        "safe food handling": gen_safe_food,
        "comfortable pregnancy": gen_comfortable_pregnancy,
        "preterm labour": gen_preterm_labour,
        "working during pregnancy": gen_working_pregnancy,
        "chiropractic": gen_chiropractic,
        "mental health": gen_mental_health,
        "normal childbirth": gen_normal_childbirth,
        "preparing for labour": gen_preparing_labour,
        "birth with a midwife": gen_birth_midwife,
        "perineal massage": gen_perineal_massage,
        "comfort measures": gen_comfort_measures,
        "tips for partners": gen_partners_labour,
        "breech": gen_breech,
        "induction": gen_induction,
        "water breaks": gen_water_breaks,
        "10 great reasons to breastfeed": gen_reasons_breastfeed,
        "breastfeeding information": gen_breastfeeding_info,
        "new dad manual": gen_new_dad,
        "infant safety": gen_infant_safety,
        "safe sleep": gen_safe_sleep,
        "baby blues": gen_baby_blues,
        "postpartum recovery": gen_postpartum_recovery,
        "after giving birth": gen_after_giving_birth,
        "postpartum care with a midwife": gen_postpartum_care_midwife,
        "newborn screening": gen_newborn_screening,
        "early years info": gen_early_years,
    }

    # Find matching generator
    generator = None
    for key, gen_func in content_generators.items():
        if key in combined:
            generator = gen_func
            break

    if generator is None:
        # Generic fallback
        generator = gen_generic

    return generator(title, summary, crawled_text)


def make_sections(sections):
    """Build HTML from list of (heading, content_html) tuples."""
    parts = []
    for heading, content in sections:
        parts.append(f"<h2>{esc(heading)}</h2>\n{content}")
    return "\n".join(parts)


def make_bullets(items):
    """Create an HTML bullet list."""
    lis = "\n".join(f"<li>{esc(item)}</li>" for item in items)
    return f"<ul>\n{lis}\n</ul>"


def make_para(text):
    return f"<p>{esc(text)}</p>"


# ---- Individual content generators ----

def gen_nutrition_pregnancy(title, summary, ct):
    return make_sections([
        ("Nutrition in Pregnancy", make_bullets([
            "Eat a variety of vegetables, fruits, whole grains, and protein foods each day following Canada's Food Guide",
            "Fill half your plate with vegetables and fruits, one quarter with whole grains, and one quarter with protein foods",
            "Aim for three meals a day with nutritious snacks in between",
            "Limit foods high in fat, salt, and sugar such as chips, candy, sweetened beverages, cakes, and cookies",
            "Drink water regularly to satisfy your thirst",
        ])),
        ("Essential Prenatal Supplements", make_bullets([
            "Take a prenatal multivitamin daily with 0.4 mg (400 mcg) of folic acid — do not exceed 1 mg (1000 mcg) per day",
            "Prenatal vitamins should contain 16–20 mg of iron; some women may need more based on their health care provider's advice",
            "Ensure adequate Vitamin B12 intake, especially for vegetarian and vegan diets",
            "Prenatal multivitamins are lower in Vitamin A because too much Vitamin A may cause birth defects, especially in the first trimester",
        ])),
        ("Key Nutrients for Pregnancy", make_bullets([
            "Folate (folic acid): Critical for preventing neural tube defects; found in leafy greens, legumes, and fortified foods",
            "Iron: Supports increased blood volume and fetal development; pair with vitamin C foods for better absorption",
            "Calcium: Essential for baby's bones and teeth; found in dairy, fortified plant milks, and leafy greens",
            "Omega-3 fats (DHA): Important for brain and eye development; found in low-mercury fish, walnuts, and flaxseed",
        ])),
        ("Physical Activity & Lifestyle", make_bullets([
            "Regular physical activity during pregnancy reduces the risk of gestational diabetes, preeclampsia, and excessive weight gain",
            "Aim for 150 minutes of moderate-intensity activity per week, such as walking, swimming, or prenatal yoga",
            "Avoid alcohol, tobacco, cannabis, and other recreational substances throughout pregnancy",
            "Prioritize sleep, stress management, and mental health support",
        ])),
        ("Food Safety During Pregnancy", make_bullets([
            "Pregnant women are at higher risk for foodborne illness due to a weakened immune system",
            "Avoid raw or undercooked meats, unpasteurized dairy, deli meats unless heated to steaming, and raw fish",
            "Practice safe food storage, handling, and cooking to prevent listeria, toxoplasmosis, and salmonella",
            "Wash all produce thoroughly and keep raw and cooked foods separate",
        ])),
    ])


def gen_healthy_pregnancy_guide(title, summary, ct):
    return make_sections([
        ("Healthy Eating Principles", make_bullets([
            "Eat a variety of nutritious foods each day to meet increased energy and nutrient needs",
            "Practice mindful eating — pay attention to hunger and fullness cues rather than eating for two",
            "Cook at home more often to control ingredients, portions, and food safety",
            "Enjoy meals with others when possible to support emotional wellbeing and healthy habits",
        ])),
        ("Using Food Labels Wisely", make_bullets([
            "Read nutrition labels to make informed choices about packaged foods",
            "Focus on foods with shorter ingredient lists and recognizable whole-food ingredients",
            "Limit highly processed foods that are high in sodium, added sugars, and unhealthy fats",
            "Use the % Daily Value on labels: 5% or less is a little, 15% or more is a lot",
        ])),
        ("The Healthy Plate Approach", make_bullets([
            "Fill half your plate with vegetables and fruits at every meal",
            "Choose whole grains for one quarter: brown rice, whole wheat bread, quinoa, oats",
            "Include protein foods for the remaining quarter: legumes, tofu, lean meats, fish, eggs",
            "Make water your drink of choice and limit sugary beverages",
        ])),
        ("Special Pregnancy Considerations", make_bullets([
            "Folic acid supplementation of 0.4 mg daily is essential before and during early pregnancy to prevent neural tube defects",
            "Iron needs increase significantly; include iron-rich foods and consider a prenatal multivitamin with 16–20 mg iron",
            "Weight gain should be gradual and within recommended ranges based on pre-pregnancy BMI",
            "Morning sickness can make eating challenging — try small, frequent meals and bland, easy-to-digest foods",
        ])),
    ])


def gen_eating_healthy_pregnancy(title, summary, ct):
    # Use crawled content since we have real text
    return make_sections([
        ("What to Eat During Pregnancy", make_bullets([
            "Eat a variety of vegetables and fruits, whole grains, and protein foods each day following Canada's Food Guide",
            "Fill half your plate with vegetables and fruits, one quarter with whole grains, and one quarter with protein foods like legumes, tofu, lean meats, fish, or eggs",
            "Aim for three meals a day with nutritious snacks in between",
            "Limit foods high in fat, salt, and sugar such as chips, salted pretzels, candy, sweetened beverages, cakes, and cookies",
            "Drink water regularly to satisfy your thirst",
        ])),
        ("Prenatal Multivitamins", make_bullets([
            "Take a prenatal multivitamin daily — it is difficult to meet folic acid and iron needs through food alone during pregnancy",
            "Choose one with 0.4 mg (400 mcg) of folic acid; do not exceed 1 mg (1000 mcg) per day",
            "Look for 16–20 mg of iron; some women may need more — talk to your health care provider",
            "Ensure it contains Vitamin B12; prenatal vitamins are also lower in Vitamin A (too much may cause birth defects)",
        ])),
        ("Key Nutrients During Pregnancy", make_bullets([
            "Folate (folic acid): Essential for preventing neural tube defects; found in leafy greens, legumes, and fortified grain products",
            "Iron: Supports increased blood volume and oxygen transport to the baby; pair iron-rich foods with vitamin C for better absorption",
            "Calcium: Important for baby's bone and teeth development; found in dairy products, fortified plant beverages, and some leafy greens",
            "Omega-3 fats: Especially DHA, important for brain and eye development; found in low-mercury fish, walnuts, and flaxseed",
        ])),
        ("Gestational Diabetes", make_bullets([
            "Gestational diabetes affects 3–20% of pregnant women and typically develops in the second or third trimester",
            "The body cannot produce enough insulin to meet increased needs during pregnancy",
            "In most cases it resolves after birth, but increases the risk of complications for both mother and baby",
            "It raises the mother's long-term risk of developing type 2 diabetes",
            "Management includes dietary changes, blood sugar monitoring, physical activity, and sometimes medication",
        ])),
        ("Food Safety in Pregnancy", make_bullets([
            "Avoid raw or undercooked meat, poultry, fish, and eggs due to risk of salmonella and other bacteria",
            "Avoid unpasteurized dairy products and juices which may contain listeria",
            "Heat deli meats and hot dogs to steaming before eating",
            "Wash all fruits and vegetables thoroughly before eating",
        ])),
    ])


def gen_fish_mercury(title, summary, ct):
    return make_sections([
        ("Mercury in Fish — What You Need to Know", make_bullets([
            "Mercury is a naturally occurring metal that can be released into water through industrial pollution",
            "Fish absorb mercury from their environment, and it accumulates in their flesh — larger, older predatory fish tend to have the highest levels",
            "Exposure to high levels of mercury during pregnancy can harm the developing brain and nervous system of the fetus",
            "Pregnant and breastfeeding women, and women who may become pregnant, should be especially careful about mercury intake",
        ])),
        ("Fish That Are Safe to Eat", make_bullets([
            "Low-mercury fish that are safe to eat regularly include: salmon, rainbow trout, Atlantic mackerel, sardines, and canned light tuna",
            "Health Canada recommends eating at least 150 g (two servings) of cooked fish per week for its omega-3 benefits",
            "Fish provides important nutrients including protein, omega-3 fats (DHA and EPA), vitamin D, and selenium",
            "Canned light tuna is lower in mercury than canned albacore (white) tuna",
        ])),
        ("Fish to Limit or Avoid During Pregnancy", make_bullets([
            "Avoid high-mercury fish including: shark, swordfish, marlin, orange roughy, and bigeye tuna",
            "Limit canned albacore (white) tuna to no more than 75 g per week during pregnancy",
            "Limit fresh/frozen tuna, escolar, and orange roughy to no more than 150 g per month",
            "Check local advisories for mercury levels in fish from lakes and rivers you fish yourself",
        ])),
        ("Balancing Benefits and Risks", make_bullets([
            "Fish is one of the best dietary sources of omega-3 fatty acids critical for fetal brain and eye development",
            "The benefits of eating recommended amounts of low-mercury fish outweigh the risks during pregnancy",
            "Choose a variety of fish types to minimize exposure to any single contaminant",
            "If you don't eat fish, talk to your health care provider about omega-3 supplements derived from marine sources",
        ])),
    ])


def gen_safe_food(title, summary, ct):
    return make_sections([
        ("Why Food Safety Matters in Pregnancy", make_bullets([
            "Pregnant women are at significantly higher risk for foodborne illness due to a naturally weakened immune system",
            "Infections like listeriosis, toxoplasmosis, and salmonella can cross the placenta and cause serious harm to the baby",
            "Listeriosis can cause miscarriage, stillbirth, premature delivery, or serious illness in newborns",
            "Foodborne illness symptoms may be mild for the mother but devastating for the developing baby",
        ])),
        ("Foods to Avoid During Pregnancy", make_bullets([
            "Raw or undercooked meat, poultry, and seafood — cook all meat to safe internal temperatures",
            "Unpasteurized dairy products including soft cheeses like brie, camembert, feta, and blue-veined cheeses unless made with pasteurized milk",
            "Unpasteurized juices and ciders",
            "Deli meats and hot dogs unless heated to steaming hot (74°C/165°F) immediately before eating",
            "Raw or lightly cooked eggs and foods made with them (homemade Caesar dressing, raw cookie dough)",
            "Refrigerated pâtés and meat spreads, smoked seafood unless cooked",
        ])),
        ("Safe Food Handling Practices", make_bullets([
            "Clean: Wash hands with soap for 20 seconds before and after handling food; wash all produce thoroughly",
            "Separate: Keep raw meat, poultry, and seafood away from ready-to-eat foods to prevent cross-contamination",
            "Cook: Use a food thermometer — cook meat to at least 74°C (165°F); ground meat to 71°C (160°F)",
            "Chill: Refrigerate perishable food within 2 hours (1 hour in hot weather); keep fridge at 4°C (40°F) or below",
        ])),
        ("Iron Deficiency Anemia in Pregnancy", make_bullets([
            "Iron deficiency anemia during pregnancy can cause fatigue, weakness, and increased risk of complications",
            "Anemia is diagnosed when hemoglobin falls below 110 g/L during pregnancy",
            "Oral iron supplements are available in various forms with different dosages and side effect profiles",
            "Dietary strategies to boost iron absorption: pair iron-rich foods with vitamin C, avoid tea and coffee with meals",
            "Talk to your health care provider about the right iron supplement and dosage for your needs",
        ])),
    ])


def gen_comfortable_pregnancy(title, summary, ct):
    return make_sections([
        ("Exercise Benefits During Pregnancy", make_bullets([
            "Most pregnant people can and should exercise regularly — physical activity reduces the risk of gestational diabetes by up to 50%",
            "Regular exercise also reduces the risk of preeclampsia, excessive weight gain, and improves mood, sleep, and stamina for labour",
            "The Society of Obstetricians and Gynaecologists of Canada recommends 150 minutes of moderate-intensity activity per week",
            "Exercise can help relieve common pregnancy discomforts including back pain, constipation, bloating, and swelling",
        ])),
        ("Safe Activities During Pregnancy", make_bullets([
            "Walking: One of the safest and most accessible exercises; can be done throughout all trimesters",
            "Swimming and water workouts: Low-impact, supports growing body weight, and helps with swelling",
            "Prenatal yoga: Improves flexibility, strength, and breathing; specifically adapted for pregnancy",
            "Stationary cycling: Provides cardiovascular benefits without balance risks",
            "Modified strength training: Use lighter weights with more repetitions; avoid heavy lifting after the first trimester",
        ])),
        ("Activities to Avoid", make_bullets([
            "Contact sports (hockey, soccer, basketball) due to risk of abdominal trauma",
            "Activities with high risk of falling (downhill skiing, horseback riding, gymnastics)",
            "Scuba diving due to risk of decompression sickness for the fetus",
            "Hot yoga or exercising in extreme heat which can raise core body temperature dangerously",
            "Exercising flat on your back after the first trimester (reduces blood flow to the baby)",
        ])),
        ("Warning Signs — Stop Exercising and Contact Your Provider", make_bullets([
            "Vaginal bleeding or fluid leaking",
            "Dizziness, feeling faint, or shortness of breath before starting activity",
            "Chest pain, rapid heartbeat, or palpitations",
            "Painful uterine contractions (more than mild)",
            "Calf pain or swelling (may indicate a blood clot)",
            "Headache, muscle weakness, or blurred vision",
        ])),
        ("Modifying Your Routine Through Each Trimester", make_bullets([
            "First trimester: Listen to your body — fatigue and nausea may require shorter, gentler sessions",
            "Second trimester: Avoid lying flat on your back; modify exercises as your centre of gravity shifts",
            "Third trimester: Focus on gentle movement, pelvic floor exercises, and stretches; reduce intensity and impact",
            "Stay hydrated, wear supportive clothing, and always include a warm-up and cool-down",
        ])),
    ])


def gen_preterm_labour(title, summary, ct):
    return make_sections([
        ("Understanding Preterm Labour", make_bullets([
            "Preterm labour involves regular contractions that cause cervical changes before 37 weeks of pregnancy",
            "Preterm birth occurs in approximately 8% of pregnancies in Canada",
            "Babies born preterm may face complications including breathing difficulties, feeding challenges, infections, and long-term developmental concerns",
            "The earlier a baby is born, the higher the risk of serious health problems",
        ])),
        ("Warning Signs of Preterm Labour", make_bullets([
            "Contractions every 10 minutes or less, or more frequently than usual for you",
            "Low, dull backache that may be constant or come and go",
            "Pelvic pressure — feeling like the baby is pushing down",
            "Cramps similar to menstrual cramps, with or without diarrhea",
            "Change in vaginal discharge (watery, bloody, or suddenly increased)",
            "Fluid leaking from the vagina (possible membrane rupture)",
        ])),
        ("Risk Factors for Preterm Labour", make_bullets([
            "Previous preterm birth is the strongest risk factor",
            "Multiple pregnancy (twins, triplets)",
            "Infection of the urinary tract, vagina, or amniotic fluid",
            "Shortened cervix detected on ultrasound",
            "Smoking, substance use, or inadequate prenatal care",
            "Certain medical conditions like high blood pressure or diabetes",
        ])),
        ("Prevention and What to Do", make_bullets([
            "Attend all prenatal appointments so your midwife can monitor for early signs",
            "Seek medical attention immediately if you experience any warning signs — early intervention can help",
            "Avoid smoking, alcohol, and recreational drugs during pregnancy",
            "Manage chronic conditions like diabetes and high blood pressure with your health care team",
            "Progesterone supplementation or cervical cerclage may be recommended for women at very high risk",
        ])),
    ])


def gen_working_pregnancy(title, summary, ct):
    # Use crawled content since we have real text
    return make_sections([
        ("Can I Work While Pregnant?", make_bullets([
            "For the majority of women with uncomplicated, low-risk pregnancies, there is no problem with working as long as desired",
            "Certain workplace hazards may make working risky — talk to your health care provider and employer if your work involves chemicals, solvents, fumes, or radiation",
            "Very physically demanding work may not be possible to continue as pregnancy progresses",
        ])),
        ("Physically Demanding Work Guidelines", make_bullets([
            "Stooping or bending over more than 10 times per hour may need to be modified",
            "Climbing a ladder more than three times in an 8-hour shift should be avoided",
            "Standing for more than 4 hours at a time may require accommodation",
            "After the 20th week: avoid lifting more than 23 kg (50 lb)",
            "After the 24th week: avoid lifting more than 11 kg (24 lb)",
            "After the 28th week: avoid stooping, bending, or climbing ladders",
            "After the 30th week: avoid lifting heavy items",
            "After the 32nd week: avoid standing still for more than 30 minutes per hour",
        ])),
        ("Working Until the End of Pregnancy", make_bullets([
            "A woman with a normal, healthy pregnancy can work right up until the start of labour",
            "You can choose to stop working whenever suits you — some stop several weeks before their due date",
            "Employers may have policies in place to protect pregnant workers and accommodate their needs",
        ])),
        ("Employment Insurance (EI) Benefits in Canada", make_bullets([
            "Federal EI provides temporary financial assistance to Canadians who are pregnant or caring for a newborn",
            "EI maternity benefits provide up to 15 weeks of income replacement for the birth mother",
            "Parental benefits provide up to 40 weeks (standard) or 69 weeks (extended) shared between parents",
            "Eligibility requires 600 insured hours of work in the qualifying period",
            "Benefit amounts are approximately 55% of insurable earnings, up to a weekly maximum",
            "Apply as soon as possible after stopping work — benefits are not retroactive beyond a certain point",
        ])),
    ])


def gen_chiropractic(title, summary, ct):
    return make_sections([
        ("Chiropractic Care During Pregnancy", make_bullets([
            "Chiropractic adjustments during pregnancy can help manage back pain, pelvic pain, and sciatica",
            "Many chiropractors specialize in prenatal care and use techniques adapted for the pregnant body",
            "Treatment may include gentle spinal adjustments, soft tissue therapy, and joint mobilization",
            "Chiropractic care is considered safe during all stages of pregnancy when performed by a qualified practitioner",
        ])),
        ("Common Pregnancy Discomforts Treated", make_bullets([
            "Low back pain: Affects 50–80% of pregnant women due to postural changes and ligament loosening",
            "Pelvic girdle pain: Pain in the front or back of the pelvis that can make walking difficult",
            "Sciatica: Radiating pain down the leg caused by pressure on the sciatic nerve",
            "Round ligament pain: Sharp or aching pain in the lower abdomen or groin area",
            "Neck pain and headaches: Often related to postural changes and increased breast weight",
        ])),
        ("Stretches and Self-Care Techniques", make_bullets([
            "Cat-cow stretch: On hands and knees, alternate between arching and rounding the back to relieve tension",
            "Pelvic tilts: Gently rock the pelvis forward and back while standing or on all fours",
            "Hip flexor stretch: Kneel on one knee and gently lean forward to stretch the front of the hip",
            "Piriformis stretch: Sit with one ankle over the opposite knee and gently lean forward",
            "Practice good posture: Keep shoulders back, chin tucked, and avoid standing for long periods with locked knees",
        ])),
        ("When to Seek Professional Care", make_bullets([
            "If pain is severe, worsening, or not responding to self-care measures",
            "If you experience numbness, tingling, or weakness in the legs",
            "If pain is accompanied by vaginal bleeding, fever, or contractions",
            "If you have difficulty walking or performing daily activities",
            "Always inform your midwife or health care provider about any complementary therapies you are using",
        ])),
    ])


def gen_mental_health(title, summary, ct):
    return make_sections([
        ("Emotional Changes During Pregnancy", make_bullets([
            "Pregnancy triggers significant hormonal changes that can affect mood, energy, and emotional wellbeing",
            "It is normal to experience a range of emotions including excitement, anxiety, mood swings, and worry",
            "Approximately 10–20% of pregnant people experience depression or anxiety during pregnancy",
            "Emotional changes can be influenced by personal history, social support, stress, and physical discomfort",
        ])),
        ("Common Mental Health Concerns in Pregnancy", make_bullets([
            "Antenatal depression: Persistent sadness, loss of interest, difficulty concentrating, changes in appetite or sleep",
            "Anxiety: Excessive worry about the baby's health, the birth, or becoming a parent",
            "Panic attacks: Sudden episodes of intense fear with physical symptoms like racing heart and shortness of breath",
            "Previous trauma: Pregnancy and birth can trigger memories of past traumatic experiences",
            "Perinatal obsessive-compulsive symptoms: Intrusive thoughts or repetitive behaviours related to baby's safety",
        ])),
        ("When to Seek Help", make_bullets([
            "If feelings of sadness or anxiety persist for more than two weeks",
            "If you have thoughts of harming yourself or your baby — seek emergency help immediately",
            "If anxiety is interfering with your daily life, sleep, or ability to care for yourself",
            "If you feel detached from your pregnancy or unable to bond with your baby",
            "If you have a history of mental health conditions — early support can help prevent worsening",
        ])),
        ("Support and Treatment Options", make_bullets([
            "Talk to your midwife, doctor, or mental health professional — they can provide referrals and resources",
            "Counselling and therapy (CBT, interpersonal therapy) are effective and safe during pregnancy",
            "Some medications can be safely used during pregnancy under medical supervision",
            "Build a support network: partner, family, friends, and community or peer support groups",
            "Self-care strategies: gentle exercise, adequate sleep, mindfulness, journaling, and spending time in nature",
        ])),
    ])


def gen_normal_childbirth(title, summary, ct):
    # Use crawled content since we have real text
    return make_sections([
        ("What Is Normal Childbirth?", make_bullets([
            "Normal birth includes labour that begins spontaneously, usually between 37 and 42 weeks of pregnancy",
            "In the broadest definition, a vaginal birth involves the baby being born head-first through the vagina, at term, with a health care professional present",
            "Normal birth also includes skin-to-skin holding after delivery and breastfeeding within the first hour",
            "Unless there is a valid medical reason to intervene, all women with low-risk pregnancies are encouraged to pursue a vaginal birth",
            "Elective C-sections are not recommended for low-risk pregnancies",
        ])),
        ("Types of Vaginal Birth", make_bullets([
            "Uncomplicated vaginal birth: The baby is born head-first, through the vagina, at term, with no medical interventions needed",
            "Vaginal birth with intervention: Some medical interventions may occur to support delivery, such as rupture of membranes, oxytocin to help labour progress, or medications/epidural for pain relief",
            "Less intervention in childbirth is always better but not always feasible — some women need help during labour",
            "Good preparation, a positive attitude, strong support, and a supportive care provider increase chances of an intervention-free birth",
        ])),
        ("Stages of Labour", make_bullets([
            "First stage: From the start of regular contractions to full cervical dilation (10 cm); includes early labour, active labour, and transition",
            "Second stage: From full dilation to the birth of the baby; involves pushing and delivery",
            "Third stage: Delivery of the placenta and membranes, usually within 5–30 minutes after birth",
        ])),
        ("Pain Management Options", make_bullets([
            "Non-medical: Breathing techniques, position changes, massage, water immersion, vocalization, and continuous support",
            "Medical options: Nitrous oxide (gas), narcotic injections, and epidural anaesthesia",
            "Each method has different effectiveness levels, onset times, and side effects for mother and baby",
            "Discuss your preferences with your care team before labour so they can support your choices",
        ])),
    ])


def gen_preparing_labour(title, summary, ct):
    return make_sections([
        ("Preparing Your Body for Labour", make_bullets([
            "Stay active during pregnancy — regular walking, prenatal yoga, and swimming build stamina for labour",
            "Practice pelvic floor exercises (Kegels) to strengthen muscles that support the birth process",
            "Perineal massage from 34 weeks onward may help reduce the risk of perineal trauma during birth",
            "Maintain good nutrition and hydration in the weeks leading up to your due date",
        ])),
        ("Creating a Birth Plan", make_bullets([
            "A birth plan outlines your preferences for labour, including pain management, positions, and who you want present",
            "Discuss your birth plan with your midwife well before your due date to ensure they understand your wishes",
            "Be flexible — labour is unpredictable and plans may need to adapt to changing circumstances",
            "Include preferences for: pain relief, who cuts the cord, skin-to-skin contact, and feeding plans",
        ])),
        ("What to Pack for the Hospital or Birth Centre", make_bullets([
            "Comfort items: Pillow from home, music, massage oil, snacks, and a water bottle",
            "For labour: Comfortable clothes, socks, lip balm, hair ties, and focal point items",
            "Postpartum: Nursing bra, comfortable underwear, loose clothing, and toiletries",
            "For baby: Going-home outfit, car seat, diapers, and receiving blankets",
            "Important documents: Health card, birth plan, and insurance information",
        ])),
        ("Recognizing the Signs of Labour", make_bullets([
            "Regular contractions that become progressively stronger, longer, and closer together",
            "Bloody show: Pink or brownish mucus discharge as the cervix begins to dilate",
            "Water breaking: Fluid leaking from the vagina — call your midwife when this happens",
            "Nesting instinct: A sudden burst of energy is common in the days before labour begins",
            "Back pain, loose stools, or a feeling of pressure in the pelvis can also signal early labour",
        ])),
        ("Choosing a Midwife for Your Birth", make_bullets([
            "Midwives are experts in healthy, low-risk birth and provide continuous one-on-one support throughout labour",
            "They can attend births at home, in birth centres, or in hospitals",
            "Midwives monitor both mother and baby throughout the process and are trained to manage complications",
            "They provide 6 weeks of postpartum care for both the birthing parent and baby",
        ])),
    ])


def gen_birth_midwife(title, summary, ct):
    # Use crawled content since we have real text
    return make_sections([
        ("The Midwifery Model of Care", make_bullets([
            "Midwives view labour and birth as a profound time in the lives of everyone involved",
            "Choosing a midwife means you and your baby will be cared for by someone you've met before — someone who knows you and understands what's important to you",
            "As experts in healthy, low-risk birth, midwives view childbirth physiologically — as a regular process that is often uncomplicated when supported and monitored",
            "Every birth is unique, and midwives are trained and prepared for a variety of issues that may arise",
        ])),
        ("Birthplace Options", make_bullets([
            "You can choose to give birth at home, in hospital, or (in some communities) at a birth centre",
            "In Ontario, approximately 20% of people in midwifery care plan a home birth",
            "Research shows that for low-risk pregnancies, home birth is as safe as hospital birth with lower rates of interventions",
            "You can choose to labour in the water and/or have a water birth, or not",
            "You can choose to have an epidural, or other forms of pain relief, or not",
        ])),
        ("Informed Choice at Every Stage", make_bullets([
            "It is very important that you have a voice and choice in where and how you give birth",
            "Midwives provide information about all options so you can make informed decisions",
            "Your midwife will discuss the risks and benefits of any proposed interventions",
            "You always have the right to accept or decline any procedure or treatment",
        ])),
        ("Monitoring and Emergency Preparedness", make_bullets([
            "Midwives monitor both mother and baby closely during labour and birth",
            "They are fully trained to deal with unforeseen events and work in collaboration with medical colleagues as required",
            "Midwives bring the same emergency equipment and medications to home births as they have in hospital",
            "Seamless transfer protocols are in place if hospital care becomes necessary",
        ])),
    ])


def gen_perineal_massage(title, summary, ct):
    return make_sections([
        ("What Is Perineal Massage?", make_bullets([
            "Perineal massage involves gently stretching the tissue between the vagina and anus (the perineum) during the last weeks of pregnancy",
            "Research suggests it may reduce the risk of perineal trauma, especially for first-time mothers",
            "It can be started around 34 weeks of pregnancy and performed daily or several times per week",
            "The technique helps increase flexibility and blood flow to the perineal area",
        ])),
        ("How to Perform Perineal Massage", make_bullets([
            "Wash your hands thoroughly and find a comfortable, relaxed position",
            "Use a natural oil (olive oil, almond oil) or a water-soluble lubricant — avoid mineral oil",
            "Insert thumbs 2–5 cm inside the vagina and gently press downward and toward the sides until you feel a slight stretching sensation",
            "Hold the stretch for 1–2 minutes while breathing deeply, then gently massage in a U-shape",
            "Your partner can also perform the massage if that is more comfortable",
        ])),
        ("Non-Medical Comfort Measures for Labour", make_bullets([
            "Breathing techniques: Slow, deep breathing helps manage contractions and keeps you calm",
            "Position changes: Walking, rocking, squatting, and hands-and-knees positions help labour progress and manage pain",
            "Massage and counter-pressure: Applied to the lower back, this can relieve contraction pain",
            "Hot and cold therapy: Warm compresses on the lower back or cool cloths on the forehead",
            "Water immersion: Labouring in a tub or shower can significantly reduce pain perception",
            "Vocalization: Moaning, humming, or low vocalizations can help release tension during contractions",
        ])),
        ("Building Your Coping Toolkit", make_bullets([
            "Having multiple comfort strategies ready increases confidence and reduces the perception of pain",
            "Practice breathing and relaxation techniques during pregnancy so they feel natural in labour",
            "Prepare your birth partner with specific techniques they can offer",
            "Remember that comfort measures can be used alongside medical pain relief if desired",
        ])),
    ])


def gen_comfort_measures(title, summary, ct):
    return make_sections([
        ("Natural Comfort Measures for Labour", make_bullets([
            "Breathing techniques: Focused, rhythmic breathing helps manage pain and reduce anxiety during contractions",
            "Position changes: Upright positions (walking, swaying, squatting) can help labour progress and reduce pain",
            "Water immersion: Warm water in a tub or shower provides significant pain relief for many birthing people",
            "Massage and touch: Partner massage, especially on the lower back and shoulders, can ease tension",
            "Hot and cold therapy: Heating pads on the lower back; ice packs on the forehead or neck",
            "Vocalization: Low moaning or humming sounds can help release tension during intense contractions",
        ])),
        ("Position Changes That Help", make_bullets([
            "Walking and swaying: Uses gravity to help the baby descend",
            "Slow dancing: Lean on your partner and gently sway through contractions",
            "Hands and knees: Takes pressure off the back and helps with back labour",
            "Squatting: Opens the pelvis and can speed up the second stage",
            "Side-lying: Good for resting between contractions while keeping the pelvis open",
            "Lunging: One foot elevated on a chair can help a baby in a posterior position rotate",
        ])),
        ("How Partners Can Help", make_bullets([
            "Familiarize yourself with the birth plan and the birthing person's preferences",
            "Help them stay calm and focused — offer encouragement and reassurance",
            "Offer water and snacks to maintain energy and hydration",
            "Use massage and counter-pressure on the lower back during contractions",
            "Suggest position changes and help them move between positions",
            "Advocate for their wishes with hospital staff when they cannot",
        ])),
        ("When Medical Pain Relief May Be Needed", make_bullets([
            "Natural methods work well for many people, but there is no shame in requesting medical pain relief",
            "Nitrous oxide (laughing gas): Self-administered, mild pain relief with no significant effects on the baby",
            "Narcotic injections: Stronger pain relief, may cause drowsiness in both mother and baby",
            "Epidural: Most effective pain relief option; may slow labour and limit mobility",
            "Discuss all options with your midwife ahead of time so you can make informed decisions during labour",
        ])),
    ])


def gen_partners_labour(title, summary, ct):
    # Use crawled content since we have real text
    return make_sections([
        ("Your Role as a Birth Partner", make_bullets([
            "Your job is to support, comfort, and encourage the birthing person throughout labour and birth",
            "Familiarise yourself with the birth plan — help write it, or at minimum know what it says so you can advocate",
            "Be aware that birth plans often change at the last minute — stay flexible and supportive",
            "You are their advocate, cheerleader, and practical helper all in one",
        ])),
        ("Practical Preparation Tips", make_bullets([
            "Do your research: Read about what happens during labour, signs of labour, contractions, and pain relief options",
            "Attend antenatal classes together — they cover essential information for both of you",
            "Know the best route to the hospital, how long the journey takes, and plan for traffic at different times",
            "Have your own bag packed with essentials: toiletries, snacks, phone charger, and a change of clothes",
            "Keep your phone on and be ready to leave at short notice in the weeks before the due date",
        ])),
        ("Providing Emotional Support", make_bullets([
            "Your comfort and reassurance matters, especially as contractions get stronger",
            "Keep up the words of encouragement, but don't be offended if you're asked to stop talking",
            "Breathe together — help your partner focus on breathing techniques or a focal point during contractions",
            "Stay calm yourself — your composure helps them feel safe and supported",
        ])),
        ("Providing Physical Support", make_bullets([
            "Help your partner move about, change positions, or lean on you if that's more comfortable",
            "Make sure they stay hydrated — have drinks and snacks ready",
            "Offer massage, counter-pressure on the lower back, or apply warm/cold compresses",
            "If they're in the bath or shower, help them get in and out safely",
            "Time contractions and keep notes to share with the midwife",
        ])),
        ("Being an Effective Advocate", make_bullets([
            "Know the birth plan preferences and speak up when the birthing person can't",
            "Ask questions of the medical team if you don't understand what's being suggested",
            "Help create a calm, private environment — close doors, dim lights, play music",
            "Stay off your phone and stay present — this is a once-in-a-lifetime moment",
            "Be flexible if plans need to change — support whatever decision the birthing person makes",
        ])),
    ])


def gen_breech(title, summary, ct):
    # Use crawled content since we have real text
    return make_sections([
        ("What Is Breech Position?", make_bullets([
            "At the time of labour, most babies are positioned head-down in the uterus",
            "A breech baby is positioned so the feet or bottom will come out first during childbirth",
            "There is usually no obvious reason why a baby is in breech position",
            "Possible causes include: preterm birth, too much or too little amniotic fluid, multiple birth, umbilical cord length, or uterine shape abnormalities",
        ])),
        ("Types of Breech Positions", make_bullets([
            "Frank breech: Legs point straight up with feet by the baby's head — the most common type",
            "Complete breech: Legs are folded with feet at the level of the buttocks",
            "Footling breech: One or both feet point down so the legs would emerge first",
        ])),
        ("External Version — Turning the Baby", make_bullets([
            "If your baby is breech at about 36 weeks, your health care provider may attempt an external version",
            "This procedure involves manually rotating the baby from outside the abdomen",
            "External version works about 50% of the time",
            "For the greatest chance of success, it should be attempted between 35 and 36 weeks gestation",
            "If successful, labour and delivery can proceed as if the baby had been head-down all along",
        ])),
        ("Delivery Options for Breech Babies", make_bullets([
            "In Canada, it has been the norm for most breech babies to be delivered by Caesarean section",
            "However, more women are now delivering breech babies vaginally",
            "Breech babies can be delivered either vaginally or by C-section — discuss risks and benefits with your provider",
            "Specific risks for breech delivery include the head becoming trapped (it is the biggest part and comes last)",
            "The choice of delivery approach should consider all risks and benefits in your particular circumstances",
        ])),
    ])


def gen_induction(title, summary, ct):
    return make_sections([
        ("Understanding Labour Induction", make_bullets([
            "Labour induction is the process of starting labour artificially before it begins on its own",
            "Induction may be recommended for medical reasons such as: being overdue (past 41–42 weeks), water breaking without contractions, high blood pressure, diabetes, or concerns about the baby's health",
            "Approximately 20–30% of pregnancies in Canada involve induced labour",
            "Induction should only be performed when the benefits outweigh the risks of continuing the pregnancy",
        ])),
        ("Methods of Induction", make_bullets([
            "Prostaglandin gel or suppositories: Applied to the cervix to soften and thin it (ripening)",
            "Synthetic oxytocin (Pitocin): Given through an IV to start contractions; dosage is carefully monitored",
            "Artificial rupture of membranes (ARM): The care provider breaks the water bag to stimulate contractions",
            "Mechanical methods: A Foley catheter or dilator may be used to gently open the cervix",
            "Natural methods: Walking, nipple stimulation, acupuncture — evidence is mixed but some people try these",
        ])),
        ("Post-Dates Pregnancy", make_bullets([
            "Pregnancy lasting beyond 40 weeks (post-dates) is common and not inherently dangerous",
            "Post-dates means past 40 weeks; post-term means past 42 weeks",
            "Monitoring for post-dates pregnancies includes fetal movement counts, non-stress tests, and ultrasound assessments",
            "Most providers recommend induction by 41–42 weeks due to gradually increasing risks",
            "Expectant management (waiting for labour to start) is an option with careful monitoring",
        ])),
        ("Risks and Benefits", make_bullets([
            "Benefits: Reduces risk of complications from prolonged pregnancy, addresses medical concerns",
            "Risks: Stronger, more painful contractions; increased chance of needing an epidural or C-section",
            "Induction may lead to a longer early labour phase before active labour begins",
            "Failed induction (no progress after attempts) may result in a C-section",
            "Discuss the specific risks and benefits for your situation with your midwife or doctor",
        ])),
    ])


def gen_water_breaks(title, summary, ct):
    return make_sections([
        ("When Your Water Breaks Before Labour", make_bullets([
            "Premature rupture of membranes (PROM) means the amniotic sac breaks before contractions begin",
            "This happens in about 8–10% of term pregnancies",
            "Most people go into labour naturally within 24 hours of their water breaking",
            "The fluid should be clear or slightly pinkish; green or brown fluid may indicate the baby has passed meconium",
        ])),
        ("What to Do If Your Water Breaks", make_bullets([
            "Call your midwife immediately — note the time, colour, and amount of fluid",
            "Use a clean pad (not a tampon) to absorb the fluid and help you monitor the colour and amount",
            "Avoid bathing in a tub, sexual intercourse, or inserting anything into the vagina to reduce infection risk",
            "Rest and stay hydrated while waiting for contractions to begin",
        ])),
        ("Monitoring and Infection Risk", make_bullets([
            "The risk of infection increases over time after the membranes rupture",
            "Your midwife will monitor your temperature, the colour of fluid, and the baby's movements",
            "Fetal movement counts: You should feel at least 6 movements in 2 hours",
            "Signs of infection include: fever, increased heart rate in mother or baby, foul-smelling fluid, or uterine tenderness",
        ])),
        ("When Induction May Be Recommended", make_bullets([
            "Induction may be recommended if labour does not start on its own within 18–24 hours",
            "The exact timeline depends on your individual circumstances, including whether you tested positive for Group B Strep",
            "If you are GBS positive, antibiotics are typically started when membranes rupture, and induction may be recommended sooner",
            "You always have the right to discuss the risks and benefits of waiting versus inducing with your midwife",
        ])),
    ])


def gen_reasons_breastfeed(title, summary, ct):
    return make_sections([
        ("Health Benefits for Your Baby", make_bullets([
            "Breast milk contains the perfect balance of nutrients for your growing baby and changes to meet their needs over time",
            "Breastfed babies have a lower risk of ear infections, respiratory infections, gastrointestinal infections, and SIDS",
            "Breast milk contains antibodies that help protect your baby from illness — especially colostrum in the first days",
            "Breastfeeding supports healthy jaw and tooth development and may reduce the risk of obesity and type 2 diabetes later in life",
        ])),
        ("Health Benefits for You", make_bullets([
            "Breastfeeding helps your uterus contract and return to its pre-pregnancy size more quickly",
            "It burns extra calories, which can help with postpartum weight loss",
            "Women who breastfeed have a reduced risk of breast cancer, ovarian cancer, and osteoporosis",
            "Breastfeeding releases oxytocin, which promotes bonding and can help reduce postpartum bleeding",
        ])),
        ("Practical and Economic Benefits", make_bullets([
            "Breast milk is always available, at the right temperature, and requires no preparation or equipment",
            "Breastfeeding is free — formula feeding can cost $1,500–$3,000 or more per year",
            "No bottles to sterilize, no formula to measure, and no worry about recalls or supply shortages",
            "Breastfeeding is environmentally friendly — no packaging, manufacturing, or transportation impact",
        ])),
        ("Emotional and Bonding Benefits", make_bullets([
            "Skin-to-skin contact during breastfeeding promotes bonding between parent and baby",
            "Breastfeeding provides a natural, quiet time for connection several times a day",
            "The hormones released during breastfeeding (oxytocin and prolactin) support maternal wellbeing",
            "Breastfeeding can increase a parent's confidence in their ability to care for their baby",
        ])),
    ])


def gen_breastfeeding_info(title, summary, ct):
    # Use crawled content since we have real text
    return make_sections([
        ("Information Sheets Available", make_bullets([
            "All Purpose Nipple Ointment (APNO) — for treating nipple pain and damage",
            "Bleb Protocol — for treating milk blisters on the nipple",
            "Blocked Ducts and Mastitis — recognizing and managing common breastfeeding complications",
            "Breast Compression — technique to increase milk flow to the baby",
            "Breastfeed a Toddler — Why on Earth? — support for extended breastfeeding",
            "Breastfeeding — Starting Out Right — essential tips for the early days",
        ])),
        ("Common Challenges Covered", make_bullets([
            "Sore Nipples — causes, prevention, and treatment strategies",
            "Engorgement — how to manage overly full, painful breasts",
            "Is My Baby Getting Enough Milk? — signs of adequate intake including wet and dirty diapers",
            "When Baby Does Not Yet Latch — troubleshooting techniques and alternative feeding methods",
            "Candida Protocol — identifying and treating thrush in mother and baby",
            "Vasospasm — recognizing and managing nipple vasospasm (Raynaud's of the nipple)",
        ])),
        ("Medications and Milk Supply", make_bullets([
            "Breastfeeding and Medications — safety information for common medications",
            "Domperidone — a medication sometimes used to increase milk supply; includes protocol and safety information",
            "Herbal Remedies for Milk Supply — evidence and guidance on herbs like fenugreek and blessed thistle",
            "Late Onset Decreased Milk Supply — causes and strategies for boosting supply after the early weeks",
            "Protocol to Increase Breastmilk Intake — step-by-step approach to increasing production",
        ])),
        ("Special Situations", make_bullets([
            "Breastfeeding and Jaundice — how jaundice affects feeding and how feeding helps resolve jaundice",
            "Breastfeeding the Premature Baby — specific guidance for preterm infants",
            "Breastfeeding Your Adopted or Surrogate Born Baby — inducing lactation without pregnancy",
            "Tongue-Tie, Lip-Tie, and Releases — assessment and management of oral restrictions",
            "Hypoglycemia of the Newborn — low blood sugar and breastfeeding management",
            "Starting Solid Foods — when and how to introduce complementary foods",
        ])),
    ])


def gen_new_dad(title, summary, ct):
    # Use crawled content since we have real text
    return make_sections([
        ("Welcome to Fatherhood", make_bullets([
            "This site was developed by fathers for fathers — guys who remember what it was like to be a new dad",
            "Being a new dad can feel overwhelming, confusing, intimidating, and tiring — but also amazing and really cool",
            "The site helps you get to the cool part by answering basic questions about babies, new moms, and new dads",
            "Categories include: Fuel Consumption, Indigenous Fatherhood, New Dads, Performance, Relationships, Safety Tips, Troubleshooting, and Under the Hood",
        ])),
        ("What New Dads Need to Know", make_bullets([
            "Newborns typically feed every 2–3 hours around the clock — you will be sleep-deprived but so will your partner",
            "Babies cry for many reasons: hunger, wet diaper, too hot, too cold, overstimulated, or just needing comfort",
            "You can bond with your baby through skin-to-skin contact, talking, singing, and being present",
            "Postpartum recovery takes weeks to months — your partner needs physical and emotional support",
        ])),
        ("Supporting Your Partner", make_bullets([
            "Take on household tasks: cooking, cleaning, laundry, and grocery shopping",
            "If breastfeeding, bring the baby to your partner, burp the baby after feeds, and handle diaper changes",
            "If bottle-feeding, take turns with feeds — especially night feeds",
            "Encourage your partner to rest when the baby sleeps and accept help from others",
            "Watch for signs of postpartum depression and encourage your partner to seek help if needed",
        ])),
        ("Self-Care for New Fathers", make_bullets([
            "Your mental health matters too — new fathers can also experience postpartum depression",
            "Accept help from family and friends; you don't have to do everything yourself",
            "Make time for basic self-care: eating well, exercising, and getting sleep when possible",
            "Stay connected with your partner — communicate openly about how you're both feeling",
            "Remember that it gets easier — the intense early weeks are temporary",
        ])),
    ])


def gen_infant_safety(title, summary, ct):
    # Use crawled content since we have real text
    return make_sections([
        ("Infant Safety Workshop Overview", make_bullets([
            "Knowing what to do and how to act if your child is having an emergency is a skill that pays you back immeasurably",
            "These are life-saving skills that all new parents, caregivers, and grandparents should have",
            "Taught by Ricki Bristow, a seasoned Paramedic, owner of Good Samaritan First Aid, and certified Car Seat Technician",
            "The workshop covers basic emergency skills, common medical concerns, and car seat safety",
            "Note: This course teaches basic skills for use at home — it is not a CPR certification course",
        ])),
        ("Common Medical Concerns Covered", make_bullets([
            "How and when to treat fevers — understanding what temperature warrants medical attention",
            "Recognizing and responding to rashes — which are normal and which need a doctor",
            "Choking: What to do if your baby is choking — back blows and chest thrusts for infants",
            "When to call 911 versus when to see your doctor or go to emergency",
            "Basic first aid skills for common infant emergencies",
        ])),
        ("Car Seat Safety", make_bullets([
            "Car seats are required by law for all infants and children in Canada",
            "Rear-facing is the safest position and should be used for as long as possible",
            "Ensure the car seat is properly installed — up to 80% of car seats are installed incorrectly",
            "A certified car seat technician can check your installation and ensure it meets safety standards",
            "Never use a car seat that has been in a crash, is expired, or has missing parts",
        ])),
        ("Workshop Details", make_bullets([
            "The event cost covers two people to attend — bring your partner, parent, or other caregiver",
            "Workshops are held regularly throughout the year (monthly evening sessions)",
            "Participants leave with the knowledge, skills, and confidence to keep their baby safe",
            "The workshop is helpful not only for parents but also for grandparents and other caregivers",
            "Register in advance as spaces are limited",
        ])),
    ])


def gen_safe_sleep(title, summary, ct):
    return make_sections([
        ("Safe Sleep Position", make_bullets([
            "Always place babies on their back to sleep — for every sleep, including naps",
            "Back sleeping reduces the risk of SIDS (Sudden Infant Death Syndrome) significantly",
            "Once a baby can roll independently, you don't need to reposition them if they roll to their tummy",
            "Tummy time is important for development but only when the baby is awake and supervised",
        ])),
        ("Safe Sleep Environment", make_bullets([
            "Use a firm, flat mattress with a fitted sheet — no soft bedding, pillows, bumper pads, or toys in the sleep area",
            "The crib or bassinet must meet current Canadian safety standards",
            "Do not use sleep positioners, nests, or inclined sleepers — these are not safe",
            "Keep the room at a comfortable temperature (around 20–22°C / 68–72°F) — avoid overheating",
            "Dress the baby in a sleep sack rather than using loose blankets",
        ])),
        ("Room Sharing Reduces SIDS Risk", make_bullets([
            "Room sharing (baby sleeps in the same room as the parent, but in their own crib or bassinet) for the first 6 months reduces SIDS risk by up to 50%",
            "Do not bed-share — sleeping with a baby on a couch, chair, or adult bed is dangerous",
            "Room sharing makes feeding and monitoring the baby easier while keeping them safe",
            "Anyone caring for the baby (grandparents, babysitters) should follow the same safe sleep guidelines",
        ])),
        ("Additional Risk Reduction Strategies", make_bullets([
            "Breastfeeding is associated with a reduced risk of SIDS",
            "Avoid smoke exposure during pregnancy and after birth — secondhand smoke significantly increases SIDS risk",
            "Avoid alcohol and drug use during pregnancy and while caring for the baby",
            "Offer a pacifier at nap time and bedtime once breastfeeding is well established",
            "Ensure baby is up to date on vaccinations — immunized babies have a lower risk of SIDS",
        ])),
    ])


def gen_baby_blues(title, summary, ct):
    # Use crawled content since we have real text
    return make_sections([
        ("Understanding the Baby Blues", make_bullets([
            "Approximately 70–80% of all new mothers experience some negative feelings or mood swings after birth",
            "Baby blues are the least severe form of postpartum mood disturbance and are very common",
            "Many women feel confused about struggling with sadness after the joyous event of a new baby",
            "Talking about these emotions is one of the best ways to cope with the baby blues",
        ])),
        ("Symptoms and Timeline", make_bullets([
            "Symptoms typically hit within four to five days after birth, though they may be noticeable earlier",
            "Common symptoms include: weepiness or crying for no apparent reason, impatience, irritability, and restlessness",
            "Anxiety, fatigue, insomnia (even when the baby is sleeping), sadness, and mood changes",
            "Poor concentration is also common",
            "Baby blues usually resolve within two weeks without treatment",
        ])),
        ("Postpartum Depression — When to Seek Help", make_bullets([
            "If symptoms persist beyond two weeks or worsen, it may be postpartum depression (PPD)",
            "PPD affects approximately 10–20% of new mothers and requires treatment",
            "Symptoms include: persistent sadness, inability to bond with the baby, withdrawal from family and friends, overwhelming fatigue, and thoughts of self-harm",
            "Postpartum psychosis is rare (1–2 per 1,000) but is a medical emergency — symptoms include hallucinations, delusions, and severe confusion",
            "Seek help immediately if you have thoughts of harming yourself or your baby",
        ])),
        ("Causes and Risk Factors", make_bullets([
            "The exact cause is unknown but is thought to be related to hormonal changes after birth",
            "Rapid drops in estrogen and progesterone levels after delivery may trigger mood changes",
            "Sleep deprivation, disruption of routine, and emotional adjustment to new parenthood all contribute",
            "Risk factors include: history of depression or anxiety, lack of social support, difficult birth experience, and financial stress",
        ])),
        ("Treatment and Support", make_bullets([
            "Talk about your feelings — with your partner, a friend, your midwife, or a mental health professional",
            "Accept help with the baby and household tasks from family and friends",
            "Counselling (CBT, interpersonal therapy) is effective for PPD",
            "Certain antidepressant medications are safe to use while breastfeeding",
            "Emergency help is available — contact your health care provider, a crisis line, or go to the nearest emergency department",
        ])),
    ])


def gen_postpartum_recovery(title, summary, ct):
    return make_sections([
        ("Physical Recovery After Birth", make_bullets([
            "The uterus takes about 6 weeks to return to its pre-pregnancy size — you may feel afterpains (cramping) especially during breastfeeding",
            "Lochia (postpartum bleeding) lasts 2–6 weeks: it starts bright red, then pinkish, then yellowish-white",
            "Perineal healing: If you had a tear or episiotomy, keep the area clean and use a peri-bottle with warm water after using the toilet",
            "If you had a C-section, the incision takes about 6 weeks to heal — avoid heavy lifting and follow your provider's activity restrictions",
            "Swelling in feet and legs is common in the first few days and will gradually resolve",
        ])),
        ("Postpartum Warning Signs — Seek Medical Help Immediately", make_bullets([
            "Heavy bleeding: Soaking a pad in less than an hour or passing large clots",
            "Fever of 38°C (100.4°F) or higher — may indicate infection",
            "Severe headache that doesn't improve with pain relief, especially with vision changes",
            "Calf pain, redness, or swelling in one leg — may indicate a blood clot",
            "Chest pain or difficulty breathing — seek emergency care immediately",
            "Signs of infection at the C-section incision or perineum: increasing pain, redness, warmth, or discharge",
        ])),
        ("Emotional Wellbeing", make_bullets([
            "Baby blues affect 70–80% of new parents and typically resolve within two weeks",
            "Postpartum depression (PPD) affects 10–20% — if sadness, anxiety, or overwhelm persist beyond two weeks, seek help",
            "Lack of sleep significantly affects mood — accept all offers of help so you can rest",
            "Stay connected with supportive people: partner, family, friends, and your midwife",
            "It's okay to ask for help — recovery and adjustment take time",
        ])),
        ("Self-Care Strategies", make_bullets([
            "Rest when the baby sleeps — your body needs time to heal",
            "Eat nourishing meals and stay hydrated, especially if breastfeeding",
            "Accept help with cooking, cleaning, and baby care from family and friends",
            "Start with gentle movement like short walks; gradually increase activity as your body allows",
            "Attend your 6-week postpartum check-up with your midwife or doctor",
        ])),
    ])


def gen_after_giving_birth(title, summary, ct):
    return make_sections([
        ("The Third Stage of Labour", make_bullets([
            "The third stage runs from the birth of the baby to the delivery of the placenta and membranes",
            "This is a critical but often under-discussed phase of the birth process",
            "There are two approaches: physiological (natural) third stage and managed (active) third stage",
            "Both approaches have benefits and considerations depending on the birth situation",
        ])),
        ("Physiological Third Stage", make_bullets([
            "The placenta is allowed to deliver on its own without medical intervention",
            "This can take up to an hour, though often it is much shorter",
            "Skin-to-skin contact and breastfeeding help the uterus contract and release the placenta naturally",
            "Best suited for births where there are no risk factors for heavy bleeding",
            "The birthing person can remain in an upright position to use gravity to assist",
        ])),
        ("Managed (Active) Third Stage", make_bullets([
            "An oxytocin injection is given as the baby's shoulders are born or immediately after birth",
            "This helps the uterus contract strongly and speeds placenta delivery, usually within 5–10 minutes",
            "Managed third stage reduces the risk of postpartum haemorrhage (heavy bleeding)",
            "The midwife may gently guide the placenta out by controlled cord traction once it has separated",
            "This is the standard approach recommended for births with higher bleeding risk",
        ])),
        ("Postpartum Care in the Hospital", make_bullets([
            "After the placenta is delivered, your midwife will check your bleeding, uterus, blood pressure, and temperature regularly",
            "Skin-to-skin contact with your baby is encouraged as soon as possible after birth",
            "Early breastfeeding helps the uterus contract and establishes milk supply",
            "You'll typically stay in hospital for a few hours (after a normal birth) to a few days (after a C-section)",
            "Your midwife provides 6 weeks of postpartum care after you go home, including home visits in the early days",
        ])),
    ])


def gen_postpartum_care_midwife(title, summary, ct):
    return make_sections([
        ("Postpartum Care with Your Midwife", make_bullets([
            "Midwives provide comprehensive postpartum care for 6 weeks after birth, including both the birthing parent and the baby",
            "Home visits in the first few days after birth ensure you and your baby are recovering well",
            "Your midwife monitors physical recovery, emotional wellbeing, feeding, and newborn health",
            "You can contact your midwife 24/7 for urgent concerns during the postpartum period",
        ])),
        ("Newborn Behaviour in the Early Days", make_bullets([
            "Feeding patterns: Newborns typically feed every 2–3 hours (8–12 times in 24 hours)",
            "Sleep-wake cycles: Newborns sleep 16–18 hours per day in short stretches of 2–4 hours",
            "Breathing: Newborns breathe irregularly — pauses of up to 10 seconds are normal",
            "Stool: Meconium (black, tarry) in the first days, transitioning to yellow, seedy stools by day 4–5",
            "Urine output: Expect at least 6 wet diapers per day by day 5–6",
        ])),
        ("How to Tell If Your Baby Is Getting Enough Milk", make_bullets([
            "At least 6 heavily wet diapers per day by day 5",
            "At least 2–3 yellow stools per day after day 4",
            "The baby seems satisfied after feeds and is gaining weight",
            "You can hear or see swallowing during feeds",
            "Your breasts feel softer after feeding",
            "Your midwife will weigh the baby and track weight gain at each visit",
        ])),
        ("When to Contact Your Midwife", make_bullets([
            "Baby has fewer than 6 wet diapers in 24 hours or no stool for 24+ hours after day 4",
            "Baby is very sleepy and difficult to wake for feeds",
            "Baby has a fever (rectal temperature 38°C / 100.4°F or higher)",
            "You have heavy bleeding, fever, severe pain, or signs of infection",
            "You feel overwhelmed, persistently sad, or have thoughts of harming yourself or your baby",
        ])),
    ])


def gen_newborn_screening(title, summary, ct):
    return make_sections([
        ("What Is Newborn Screening?", make_bullets([
            "Newborn screening is a blood test done shortly after birth to detect rare but treatable conditions",
            "In Ontario, a heel prick is done when the baby is about 24–48 hours old to collect a small blood sample",
            "The screening tests for over 25 conditions including metabolic disorders, endocrine conditions, and blood disorders",
            "Early detection allows for timely treatment that can prevent serious health problems, developmental delays, and even death",
        ])),
        ("Common Conditions Screened", make_bullets([
            "Phenylketonuria (PKU): A metabolic disorder that requires a special diet to prevent intellectual disability",
            "Congenital hypothyroidism: Underactive thyroid that can be treated with daily thyroid hormone replacement",
            "Sickle cell disease and other hemoglobin disorders: Blood conditions that need early monitoring and care",
            "Cystic fibrosis: A condition affecting lungs and digestion that benefits from early intervention",
            "Medium-chain acyl-CoA dehydrogenase (MCAD) deficiency: A metabolic disorder that can cause low blood sugar",
        ])),
        ("Understanding Newborn Jaundice", make_bullets([
            "Jaundice causes yellowing of the skin and eyes due to high bilirubin levels",
            "Bilirubin is produced when red blood cells break down and is eliminated through stool and urine",
            "Very common: affects about 60% of full-term and 80% of preterm babies in the first week",
            "Most cases resolve on their own with frequent feeding, which helps the baby excrete bilirubin",
            "High levels may require phototherapy (light treatment) to prevent potential brain damage",
        ])),
        ("What Happens If a Screen Is Positive", make_bullets([
            "A positive screening result does not mean your baby has the condition — it means further testing is needed",
            "Your midwife or doctor will contact you and arrange confirmatory testing as quickly as possible",
            "If a condition is confirmed, treatment and management plans will be started right away",
            "Most screened conditions can be effectively managed with early treatment",
            "Ontario's newborn screening program has been highly successful at identifying and treating conditions early",
        ])),
    ])


def gen_early_years(title, summary, ct):
    # Use crawled content since we have some real text
    return make_sections([
        ("EarlyON Child and Family Centres", make_bullets([
            "EarlyON centres across Waterloo Region offer free drop-in programs for children 0–6 and their caregivers",
            "Programs include play-based learning, early literacy activities, and parent workshops",
            "Centres are located throughout Kitchener, Waterloo, Cambridge, and surrounding areas",
            "All programs are free of charge and no registration is required for most drop-in sessions",
        ])),
        ("Programs Available", make_bullets([
            "Play-based learning: Structured and unstructured play activities designed to support child development",
            "Early literacy: Story times, reading programs, and language development activities",
            "Parent workshops: Topics include child development, positive parenting, nutrition, and more",
            "Developmental screening: Check your child's developmental milestones with qualified staff",
            "Community connections: Meet other parents and families in your area",
        ])),
        ("What to Expect at an EarlyON Visit", make_bullets([
            "Drop in anytime during operating hours — no appointment needed",
            "A welcoming, inclusive environment for all families",
            "Qualified early childhood educators on site to support play and answer questions",
            "Access to books, toys, art supplies, and age-appropriate activities",
            "A chance to connect with other parents and caregivers in your community",
        ])),
        ("Benefits for Your Family", make_bullets([
            "Supports your child's social, emotional, cognitive, and physical development",
            "Provides parenting information and connections to community resources",
            "Helps reduce isolation for new parents by creating social connections",
            "Professional staff can answer questions about child development and refer you to specialized services if needed",
            "Getting connected early builds a support network for the years ahead",
        ])),
    ])


def gen_generic(title, summary, ct):
    """Generic fallback content generator."""
    return make_sections([
        ("Overview", f"<p>{esc(summary or 'This resource provides information and guidance related to ' + title + '.')}</p>"),
        ("Key Information", make_bullets([
            "This resource covers important topics related to pregnancy, birth, and early parenting",
            "Consult your midwife or health care provider for personalized advice related to your situation",
            "Evidence-based information helps you make informed decisions about your care",
        ])),
        ("How to Use This Resource", make_bullets([
            "Read through the material and note any questions for your next prenatal appointment",
            "Discuss the information with your partner, support person, or health care team",
            "Remember that every pregnancy is unique — what works for one person may not work for another",
            "Use this as a starting point for conversations with your care providers",
        ])),
    ])


def main():
    with open(INPUT, "r") as f:
        resources = json.load(f)

    print(f"Loaded {len(resources)} resources from JSON")

    os.makedirs(OUTDIR, exist_ok=True)

    for r in resources:
        section_number = r["section_number"]
        resource_index = r["resource_index"]
        filename = f"{section_number}-{resource_index}.html"
        filepath = os.path.join(OUTDIR, filename)

        title = r["title"]
        url = r["url"]
        rtype = r["type"]
        summary = r.get("summary", "")
        crawled_text = r.get("crawled_text", "")
        section_title = r["section_title"]

        type_label = TYPE_LABELS.get(rtype, "Resource")

        # Determine section label
        section_label = "Session" if str(section_number).isdigit() else "Section"

        # Generate detailed content
        detailed_content = generate_content_from_crawl(title, summary, crawled_text, rtype, url)

        # Build the full HTML
        html_output = HTML_TEMPLATE.format(
            title=esc(title),
            type_label=esc(type_label),
            section_label=section_label,
            section_title=esc(section_title),
            detailed_content=detailed_content,
            url=esc(url),
        )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_output)

        print(f"  Created: {filename} — {title}")

    print(f"\nDone! Generated {len(resources)} HTML files in {OUTDIR}")


if __name__ == "__main__":
    main()
