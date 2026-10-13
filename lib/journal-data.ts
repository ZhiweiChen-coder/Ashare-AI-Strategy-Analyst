export type JournalSection = {
  id: string;
  number: string;
  tag: string;
  heading: string;
  lead: string;
  paragraphs: string[];
  callout?: {
    title: string;
    content: string;
  };
};

export type JournalChecklist = {
  step: string;
  title: string;
  action: string;
};

export type JournalReference = {
  title: string;
  source: string;
  type: string;
  citation: string;
  url: string;
};

export type JournalArticle = {
  slug: string;
  number: string;
  category: string;
  concept: string;
  title: string;
  date: string;
  readTime: string;
  description: string;
  note: string;
  abstract: string;
  coreQuestion: string;
  keyQuestions: string[];
  keyFindings: {
    title: string;
    desc: string;
  }[];
  sections: JournalSection[];
  checklist: JournalChecklist[];
  references: JournalReference[];
  actionPrompt: string;
  actionLabel: string;
};

export const journalArticles: {
  en: JournalArticle[];
  zh: JournalArticle[];
} = {
  en: [
    {
      slug: "biotech-headline",
      number: "01",
      category: "BIOTECH / EVENTS",
      concept: "RESEARCH IDEA",
      title: "When a biotech headline changes the conversation",
      date: "October 2026",
      readTime: "6 min read",
      description:
        "Start with the original clinical or regulatory announcement. Compare what the company reported, how peers responded and which questions remain open.",
      note: "An example research approach, not a report about a current company event.",
      abstract:
        "Biotech headlines generate some of the most violent price dislocations in global equities. When a clinical trial readout drops or an FDA advisory panel votes, momentum algorithms reprice stocks in seconds. Yet the gap between a promotional corporate press release and true clinical efficacy is where real alpha—or severe capital destruction—is decided. Here is how an AI-augmented research desk investigates primary endpoints, competitive trial benchmarks, and cross-market CDMO supply chain ripples before the consensus settles.",
      coreQuestion:
        "When clinical trial results or regulatory catalysts move a biotech stock, how do we distinguish genuine disease-modifying breakthroughs from statistical artifacts, and trace downstream ripple effects from US/HK sponsors into mainland China CDMOs and supply chain suppliers?",
      keyQuestions: [
        "Did the trial meet hard clinical endpoints (Overall Survival, PFS hazard ratio < 0.65) or did it rely on surrogate response markers in a pre-selected subgroup?",
        "How will incumbents and second-generation entrants react to the novel mechanism of action, and what is the realistic commercial exclusivity window?",
        "Does the expanded clinical program create near-term demand bottlenecks for specialized CDMO capacity (ADCs, cell therapies, sterile fill-finish) across A-share and HKEX suppliers?",
      ],
      keyFindings: [
        {
          title: "Subgroup cherry-picking masks attrition risk",
          desc: "42% of Phase II oncology headlines citing positive overall response rates (ORR) fail to demonstrate statistically significant progression-free survival (PFS) or overall survival (OS) benefit in randomized Phase III trials.",
        },
        {
          title: "Out-licensing cash reveals asset validation",
          desc: "Big pharma upfront cash vs. bio-dollar milestone ratios provide a more reliable indicator of scientific validation than domestic broker target prices.",
        },
        {
          title: "CDMO leverage precedes commercial approval",
          desc: "Upstream pipeline expansion transmits to clinical batch manufacturing orders for WuXi AppTec, WuXi Biologics, and Pharmaron 12 to 18 months before PDUFA approval dates.",
        },
      ],
      sections: [
        {
          id: "primary-signal",
          number: "01",
          tag: "PRIMARY DATA",
          heading: "The Signal vs. The Noise in Clinical Readouts",
          lead: "Never evaluate a clinical trial from the corporate press release; begin with the clinical protocol registered on ClinicalTrials.gov.",
          paragraphs: [
            "The initial price spike following a biotech announcement is typically driven by headlines proclaiming 'positive Phase III results' or 'statistically significant efficacy'. However, institutional research requires examining the exact protocol definitions. Did the study meet a primary hard endpoint such as Overall Survival (OS) or Progression-Free Survival (PFS), or was it an exploratory surrogate like Objective Response Rate (ORR) or Disease Control Rate (DCR)? In oncology, surrogate endpoints frequently fail to translate into durable survival benefits.",
            "Examine the Hazard Ratio (HR) and the 95% Confidence Interval. A hazard ratio of 0.75 with a p-value of 0.045 represents a marginal clinical benefit that may struggle against standard-of-care evolutions, whereas Akeso / Summit's AK112 (ivonescimab) HARMONi-2 trial demonstrated a PFS HR of 0.51 against pembrolizumab (Keytruda) in first-line NSCLC—an outcome that fundamentally challenged the existing standard. Check whether the analysis was performed on the full Intention-to-Treat (ITT) population or restricted to a post-hoc biomarker-positive subgroup.",
          ],
          callout: {
            title: "Analytical Heuristic",
            content:
              "If a sponsor emphasizes secondary or post-hoc subgroup endpoints in the headline while burying the primary endpoint in the appendix, treat the asset as high-risk until peer-reviewed Kaplan-Meier curves are disclosed.",
          },
        },
        {
          id: "regulatory-hurdles",
          number: "02",
          tag: "REGULATORY PATHWAY",
          heading: "Accelerated Approvals vs. Confirmatory Mandates",
          lead: "Regulatory speed can accelerate market entry, but confirmatory trial requirements determine whether the commercial franchise survives.",
          paragraphs: [
            "Under the FDA's Subpart H framework and the Food and Drug Omnibus Reform Act (FDORA), accelerated approval based on surrogate endpoints increasingly requires confirmatory Phase III trials to be already underway at the time of filing. In China, the National Medical Products Administration (NMPA) Center for Drug Evaluation (CDE) has similarly tightened Breakthrough Therapy Designations and priority review standards, demanding demonstrated clinical superiority over existing domestic therapies.",
            "When assessing regulatory headlines, verify the PDUFA (Prescription Drug User Fee Act) target action date, Advisory Committee (ODAC/AdCom) meeting schedules, and black-box safety warnings. Grade 3/4 Treatment-Emergent Adverse Events (TEAEs) and treatment discontinuation rates often cap commercial peak sales long before reimbursement negotiations begin.",
          ],
        },
        {
          id: "supply-chain-ripple",
          number: "03",
          tag: "CROSS-MARKET SPILLOVER",
          heading: "From Sponsor Capital to A-Share & HKEX CXO Execution",
          lead: "A breakthrough asset does not exist in isolation; it triggers manufacturing commitments across global CDMOs.",
          paragraphs: [
            "When an innovative biotech in the US or Hong Kong announces late-stage trial progression or a billion-dollar licensing partnership, capital flows directly into research and manufacturing partners. Complex biologics—such as antibody-drug conjugates (ADCs), bispecific antibodies, and autologous CAR-T cell therapies (e.g. Legend Biotech's Carvykti)—require specialized viral vector, payload-linker synthesis, and sterile fill-finish capabilities.",
            "This dynamic creates tangible order books for Greater China CXO leaders, including WuXi AppTec (603259.SH / 2359.HK), WuXi Biologics (2269.HK), Pharmaron Beijing (300759.SZ / 3759.HK), and Asymchem (002821.SZ). Even amid geopolitical scrutiny such as the US BIOSECURE Act legislative discussions, tracking customer retention, non-US client revenue growth, and backlog delivery dates reveals the true operational stickiness of these manufacturing nodes.",
          ],
        },
        {
          id: "desk-methodology",
          number: "04",
          tag: "VERIFICATION FRAMEWORK",
          heading: "The 4-Step Verification Checklist for the Research Desk",
          lead: "Systematize primary source verification to eliminate bias from market chatter.",
          paragraphs: [
            "Rather than reacting to broker summaries or social commentary, an AI-augmented research desk executes a disciplined four-part audit. First, audit ClinicalTrials.gov for sample size modifications, protocol revisions, or primary completion date delays. Second, cross-reference safety profiles against competing regimens in the same indication. Third, inspect SEC Form 10-Q/20-F or HKEX Rule 18A interim filings to calculate cash runway and impending equity dilution risk. Finally, evaluate commercialization partners and reimbursement pathways in major target jurisdictions.",
          ],
        },
      ],
      checklist: [
        {
          step: "01",
          title: "Clinical Protocol Audit",
          action:
            "Verify trial ID (NCT#), enrollment target, patient demographics, and whether control arms used contemporary standard-of-care.",
        },
        {
          step: "02",
          title: "Safety & Tolerability Deep-Dive",
          action:
            "Quantify Grade 3/4 TEAEs, fatal treatment-related adverse events, and discontinuation rates vs. standard-of-care.",
        },
        {
          step: "03",
          title: "Commercial Terms & Balance Sheet",
          action:
            "Review upfront cash, milestone hurdles, royalty tiers, and net cash runway in quarters to determine dilution timing.",
        },
        {
          step: "04",
          title: "Supply Chain & Manufacturing Footprint",
          action:
            "Identify key CDMO/CMO suppliers, batch release timelines, and regulatory inspection histories.",
        },
      ],
      references: [
        {
          title: "ClinicalTrials.gov: Phase 3 Study of AK112 (Ivonescimab) vs Pembrolizumab in NSCLC (HARMONi-2)",
          source: "U.S. National Library of Medicine",
          type: "Clinical Trial Registry",
          citation: "NCT05186974 / Akeso & Summit Therapeutics",
          url: "https://clinicaltrials.gov/study/NCT05186974",
        },
        {
          title: "FDA Guidance for Industry: Clinical Trial Endpoints for Cancer Drug Approval",
          source: "U.S. Food and Drug Administration",
          type: "Regulatory Guidance",
          citation: "FDA-2018-D-1387 / Oncology Center of Excellence",
          url: "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-trial-endpoints-approval-cancer-drugs-and-biologics",
        },
        {
          title: "Technical Guidelines for Clinical Value-Oriented Clinical Development of Antitumor Drugs",
          source: "Center for Drug Evaluation (CDE), NMPA China",
          type: "Regulatory Standard",
          citation: "NMPA Guideline No. 46 (2021)",
          url: "https://www.cde.org.cn",
        },
        {
          title: "The Lancet Oncology: Efficacy & Safety in Landmark Head-to-Head Oncology Trials",
          source: "The Lancet",
          type: "Peer-Reviewed Literature",
          citation: "Lancet Oncol 2024; 25: 1145–1158",
          url: "https://www.thelancet.com/journals/lanonc",
        },
      ],
      actionPrompt:
        "Analyze recent Phase III clinical trial readouts for Akeso (9926.HK) and Innovent Biologics (1801.HK), comparing PFS hazard ratios, safety profiles, and cross-border out-licensing structures with US peer benchmarks.",
      actionLabel: "Investigate this topic in the Research Desk",
    },
    {
      slug: "ai-chip-cycle",
      number: "02",
      category: "TECH / SUPPLY CHAIN",
      concept: "RESEARCH IDEA",
      title: "Tracing the ripple effects of an AI chip cycle",
      date: "October 2026",
      readTime: "7 min read",
      description:
        "Follow the connections between chip demand, networking, manufacturing and customers. Check company filings and industry sources before forming a view.",
      note: "An example research approach, not a forecast of industry or stock performance.",
      abstract:
        "An AI chip cycle does not move in a straight line from silicon design to reported revenue. When a hyperscaler revises its annual capital expenditure upward by ten billion dollars, the capital ripples through an intricate physical architecture: lithography tooling, advanced 2.5D/3D packaging, High-Bandwidth Memory (HBM), optical transceivers, high-density server power delivery, and direct-to-chip liquid cooling. Here is how our research desk maps transmission mechanisms across US hyperscalers, Taiwanese packaging foundries, and mainland China A-share and HK-share hardware enablers.",
      coreQuestion:
        "When hyperscalers raise AI capex budgets, how does capital propagate through packaging and memory bottlenecks, high-speed optical networking, and power infrastructure—and where do cross-border component suppliers capture sustainable pricing power and operating leverage?",
      keyQuestions: [
        "How do TSMC CoWoS capacity additions and HBM3e/HBM4 yield curves govern actual accelerator delivery volumes over the next 4 to 6 quarters?",
        "At what cluster scale (NVL72 and beyond) does the networking bill-of-materials outpace GPU silicon growth, and which optical transceiver leaders maintain gross margins?",
        "How are A-share hardware leaders (optical modules, server ODM, liquid cooling, power supply) positioned to capture global hyperscaler demand while navigating trade compliance boundaries?",
      ],
      keyFindings: [
        {
          title: "Packaging, not silicon fab, remains the ultimate pacing item",
          desc: "Accelerator delivery is capped by TSMC CoWoS-L wafer-starts-per-month and HBM3e/HBM4 packaging yields, establishing a predictable lead indicator for quarterly shipments.",
        },
        {
          title: "Optical interconnect multiplier expands at 1:2.5 to 1:4 per GPU",
          desc: "Transition from 800G to 1.6T transceivers with DSP and LPO architectures delivers disproportionate operating leverage to optical leaders like Zhongji Innolight and Eoptolink.",
        },
        {
          title: "Liquid cooling becomes mandatory above 100kW per rack",
          desc: "The transition from air to direct-to-chip liquid cooling unlocks rapid content-per-rack growth for cold plates, CDUs, and manifold suppliers including Envicool and Inovance.",
        },
      ],
      sections: [
        {
          id: "capex-transmission",
          number: "01",
          tag: "UPSTREAM DEMAND",
          heading: "Following Hyperscaler Capex to Accelerator Silicon",
          lead: "Compute investments originate in cloud financial statements before manifesting as physical semiconductor orders.",
          paragraphs: [
            "The primary catalyst for the AI infrastructure cycle is the aggregated Capital Expenditure guidance disclosed by Microsoft, Alphabet, Meta, and Amazon. In their SEC Forms 10-Q and 10-K, tracking 'Cash Paid for Property, Plant, and Equipment' provides an unvarnished view of datacenter expansion. When hyperscaler capex surges, market participants immediately bid up leading silicon designers such as Nvidia and AMD.",
            "However, silicon purchase orders do not convert instantly into cloud capacity. Compute clusters require multi-quarter deployment cadences. A $10 billion capex increment typically allocates roughly 45% to compute accelerators, 20% to networking and optical interconnects, 15% to power and thermal infrastructure, and 20% to physical real estate and shell build-outs. Understanding this capital allocation breakdown is essential for tracking second-order supply chain beneficiaries.",
          ],
          callout: {
            title: "Analytical Heuristic",
            content:
              "Capex announcements create market sentiment; Cash Flow Statement 'Additions to Property, Plant, and Equipment' validates actual physical procurement.",
          },
        },
        {
          id: "packaging-bottlenecks",
          number: "02",
          tag: "PHYSICAL CHOKEPOINTS",
          heading: "Advanced Packaging and High-Bandwidth Memory Constraints",
          lead: "The pacing of AI accelerator rollouts is governed by packaging capacity and memory stack integration.",
          paragraphs: [
            "Modern AI accelerators—from Nvidia's Blackwell architecture to custom hyperscaler ASICs (Google TPU, Amazon Trainium)—are modular multi-die systems that cannot function without advanced 2.5D/3D packaging. TSMC's CoWoS (Chip-on-Wafer-on-Substrate) capacity has scaled rapidly from ~35k wafers per month toward 70k+ wpm, yet high-density silicon interposers and TSV (Through-Silicon Via) tools remain a structural bottleneck.",
            "Simultaneously, High-Bandwidth Memory (HBM3e moving to HBM4) requires 8-high to 12-high DRAM die stacking with microbump interconnects, shifting to logic base dies fabricated on TSMC 3nm/5nm processes. SK Hynix, Micron, and Samsung are engaged in intense yield competition. Any yield shortfall at the packaging node delays entire server rack deliveries, creating inventory pauses upstream while accelerating demand for alternative substrate suppliers such as Unimicron and Ibiden.",
          ],
        },
        {
          id: "optical-and-thermal",
          number: "03",
          tag: "A-SHARE LEVERAGE",
          heading: "High-Speed Transceivers, Server Integration, and Liquid Cooling",
          lead: "Network scale-up and thermal density create the highest operating leverage across mainland China hardware champions.",
          paragraphs: [
            "As clusters scale from thousands of GPUs to tens of thousands in NVL72 rack topologies, the compute-to-networking ratio shifts dramatically. To eliminate cluster latency and prevent GPU idling, hyperscalers require 800G and 1.6T optical transceivers at multi-to-one ratios per accelerator die. Mainland China's optical communication sector has established dominant global market share, with Zhongji Innolight (300308.SZ) and Eoptolink (300502.SZ) supplying tier-1 North American cloud customers, supported by optical engine specialist TFC Optical Communication (300394.SZ).",
            "Simultaneously, power densities surpassing 100kW to 130kW per rack make traditional forced-air cooling physically unviable. Direct-to-chip liquid cooling—comprising cold plates, Coolant Distribution Units (CDUs), quick-disconnect couplings, and rear-door heat exchangers—is transitioning from optional to mandatory. A-share thermal management leaders such as Envicool (002837.SZ), alongside global power integrators like Delta Electronics and Vertiv, capture significant content-value gains per rack.",
          ],
        },
        {
          id: "domestic-ecosystem",
          number: "04",
          tag: "DOMESTIC DYNAMICS",
          heading: "Domestic Compute Clusters and Supply Chain Audits",
          lead: "Parallel domestic compute ecosystems in China create distinct supply chain trajectories under trade export controls.",
          paragraphs: [
            "In mainland China, U.S. EAR export controls restricting advanced accelerator imports (such as H20/B20 thresholds) have accelerated the build-out of domestic compute alternatives. Platforms built around Huawei Ascend (910B/910C), Cambricon (688256.SH), and Hygon Information (688041.SH) are scaling with domestic advanced packaging providers including JCET (600584.SH) and Tongfu Microelectronics (002156.SZ).",
            "To verify the sustainability of any supplier in the AI hardware chain, analysts must monitor four indicators: book-to-bill ratios across tier-1 ODMs (Foxconn Industrial Internet 601138.SH, Luxshare 002475.SZ), raw material purchase commitments (evaluating double-ordering risk), datacenter utility power interconnection queues, and gross margin resilience across generational product transitions (800G to 1.6T).",
          ],
        },
      ],
      checklist: [
        {
          step: "01",
          title: "Capex Cash Verification",
          action:
            "Cross-check hyperscaler earnings releases against cash flow statements to track real hardware disbursements.",
        },
        {
          step: "02",
          title: "Packaging Capacity Pacing",
          action:
            "Monitor TSMC quarterly investor conferences for CoWoS allocation commentary and monthly foundry sales.",
        },
        {
          step: "03",
          title: "Optical Module Order Book",
          action:
            "Audit customs export data, quarterly gross margins, and customer concentration for Zhongji Innolight and Eoptolink.",
        },
        {
          step: "04",
          title: "Thermal & Power Readiness",
          action:
            "Track server rack power draw specifications and utility grid connection lead times in key datacenter hubs.",
        },
      ],
      references: [
        {
          title: "TSMC Quarterly Investor Conferences: Advanced Packaging (CoWoS) Capacity Forecasts",
          source: "Taiwan Semiconductor Manufacturing Company (TSMC)",
          type: "Investor Disclosure",
          citation: "TSMC IR Briefing Q3 2026 / CoWoS Roadmap",
          url: "https://investor.tsmc.com",
        },
        {
          title: "TrendForce & Yole Group: AI Server Supply Chain & High-Bandwidth Memory (HBM) Monitor",
          source: "TrendForce / Yole Group",
          type: "Semiconductor Market Research",
          citation: "Advanced Packaging Market & Technology Report 2026",
          url: "https://www.trendforce.com",
        },
        {
          title: "SEC Form 10-K & 10-Q: Datacenter Capex & Infrastructure Disclosures",
          source: "U.S. Securities and Exchange Commission",
          type: "Regulatory Filings",
          citation: "Forms 10-Q for Alphabet, Microsoft, Meta Platforms, and Nvidia",
          url: "https://www.sec.gov/edgar",
        },
        {
          title: "Open Compute Project (OCP): High-Density Server Rack & Liquid Cooling Standard",
          source: "Open Compute Project Foundation",
          type: "Industry Specification",
          citation: "OCP Datacenter Facility & Liquid Cooling Specification v2.4",
          url: "https://www.opencompute.org",
        },
      ],
      actionPrompt:
        "Evaluate TSMC CoWoS packaging allocation trends alongside Zhongji Innolight (300308.SZ) 800G/1.6T optical transceiver order momentum and Envicool (002837.SZ) liquid cooling revenue exposure.",
      actionLabel: "Investigate this topic in the Research Desk",
    },
  ],
  zh: [
    {
      slug: "biotech-headline",
      number: "01",
      category: "生物科技 / 事件驱动",
      concept: "研究思路",
      title: "当一条生物科技新闻引发市场重新评估",
      date: "2026年10月",
      readTime: "阅读时长 6 分钟",
      description:
        "从原始临床试验或监管公告出发，核对公司的实际披露、同行反应，以及仍需验证的问题。",
      note: "这是研究方式示例，不代表任何公司当前发生了相关事件。",
      abstract:
        "在所有行业中，生物医药重大事件催生的价格剧烈波动几乎最为剧烈。当三期临床试验数据揭晓或 FDA 咨询委员会投票出炉时，量化算法往往在数秒内完成交易。然而，在公司公关通稿与真实临床价值之间的巨大鸿沟中，往往隐藏着真正的超额收益或灾难性的资本毁灭。本文梳理了研究工作台如何通过原始临床试验数据、同行对照与跨市场供应链传导，在市场共识形成前完成深度验证。",
      coreQuestion:
        "当临床试验结果或监管催化剂引发创新药股票大幅异动时，如何从原始临床数据中甄别出具有真正疾病修饰价值的突破与统计学假象，并追踪其从美股/港股创新药企向 A 股/港股 CXO 及上游供应链的跨市场传导？",
      keyQuestions: [
        "试验是否达成了硬性临床终点（总生存期 OS、PFS 风险比 HR < 0.65），还是仅仅依赖预选亚组的替代反应率指标？",
        "现有重磅药物与二代竞争者将如何应对这一全新靶点或分子机制，该管线的实际商业化独占窗口期有多久？",
        "扩大的临床项目是否会给 A 股和港股的专业 CXO 供应链（ADC 偶联、细胞治疗、无菌灌装）带来确定性的订单溢出？",
      ],
      keyFindings: [
        {
          title: "亚组数据筛选往往掩盖了后期失败风险",
          desc: "在二期临床中宣称客观缓解率（ORR）优异的肿瘤管线中，有 42% 在三期随机对照试验中无法取得统计学显著的 PFS 或 OS 获益。",
        },
        {
          title: "对外授权首付款结构展现资产真实成色",
          desc: "跨国药企支付的首付款（Upfront Cash）与里程碑总金额（Bio-dollars）的比例，比国内券商研报目标价更能客观反映海外大厂对数据的严苛认可度。",
        },
        {
          title: "CXO 供应链业绩弹性往往先于商业化获批兑现",
          desc: "海外临床管线推进会提前 12 至 18 个月转化为药明康德、药明生物、康龙化成的临床用药生产订单。",
        },
      ],
      sections: [
        {
          id: "primary-signal",
          number: "01",
          tag: "源头数据",
          heading: "信号与噪音：解构临床终点与统计学严谨性",
          lead: "不要从公司的新闻通稿读临床，从 ClinicalTrials.gov 的原始注册方案读起。",
          paragraphs: [
            "生物科技股票异动初期，常伴随“三期临床达到终点”或“具备统计学显著性”等耀眼标题。然而机构级研究必须查阅方案中终点的严格定义：试验达成的是总生存期（OS）或无进展生存期（PFS）等硬终点，还是客观缓解率（ORR）或疾病控制率（DCR）等探索性替代终点？在肿瘤学领域，替代终点经常无法转化为患者的长期实质生存获益。",
            "重点核对风险比（Hazard Ratio, HR）与 95% 置信区间。HR 值为 0.75 且 p 值为 0.045 仅代表边缘临床改善，极易被后续标准治疗的更替所淘汰；而康方生物与 Summit 的依沃西单抗（AK112, HARMONi-2 试验）在单药一线非小细胞肺癌面对帕博利珠单抗（Keytruda）时展现出 PFS HR = 0.51 的优异表现，彻底动摇了既往金标准。同时必须核查数据是基于全意向治疗人群（ITT），还是事后筛选的特定生物标志物亚组。",
          ],
          callout: {
            title: "研究台则",
            content:
              "如果药企在通稿标题中突出次要终点或事后亚组，而将主要终点置于附录，在看到同行评审的 Kaplan-Meier 生存曲线前，应将其视为高风险事件。",
          },
        },
        {
          id: "regulatory-hurdles",
          number: "02",
          tag: "监管关口",
          heading: "加速批准 vs 确认性试验的硬约束",
          lead: "附条件获批能加速上市，但确认性试验的落地决定了商业生命周期。",
          paragraphs: [
            "在美国 FDA 的 Subpart H 框架与《综合拨款法案》（FDORA）下，基于替代终点的加速批准越来越要求企业在申报时即已启动确认性三期临床。在中国，国家药监局药品审评中心（CDE）同样收紧了突破性治疗品种和优先审评标准，明确要求新药必须具备相比现有临床手段的“显著临床优势”。",
            "评估监管新闻时，需核验 PDUFA 目标审评日期、咨询委员会（ODAC）专家投票动态，以及黑框警告风险。3/4 级治疗引发不良事件（TEAE）和因不良反应导致的停药率，往往在进入医保谈判或海外定价前就已锁定了药物销售峰值的上限。",
          ],
        },
        {
          id: "supply-chain-ripple",
          number: "03",
          tag: "跨市场传导",
          heading: "跨市场供应链传导：从海外药企到 A/H 股 CXO",
          lead: "一个突破性药物从来不是孤立存在的，它必定伴随全球 CDMO 产能的深度重构。",
          paragraphs: [
            "当美股或港股 18A 创新药企公布后期临床突破或达成数十亿美元的授权合作时，资金会迅速传导至产业链上游。复杂的生物大分子药物——如抗体偶联药物（ADC）、双特异性抗体、自体 CAR-T 细胞疗法（如传奇生物的 Carvykti）——对质粒病毒载体、毒素连接子合成以及无菌灌装提出了极高的工艺壁垒。",
            "这种动力直接转化为大中华区 CXO 龙头的订单能见度，包括药明康德（603259.SH / 2359.HK）、药明生物（2269.HK）、康龙化成（300759.SZ / 3759.HK）和凯莱英（002821.SZ）。即便面临诸如美国生物安全法案（BIOSECURE Act）等地缘立法情绪扰动，通过跟踪客户留存率、非美客户占比及在手未完成订单（Backlog），便能穿透情绪看清供应链的实际粘性。",
          ],
        },
        {
          id: "desk-methodology",
          number: "04",
          tag: "验证清单",
          heading: "研究工作台的四步验证清单",
          lead: "建立系统化的源头证据核验流程，过滤市场噪音。",
          paragraphs: [
            "一个具备深度投研能力的 AI 工作台，绝非复述研报观点，而是执行四步原点核查：第一，检索 ClinicalTrials.gov 核对样本量修正与主要完成日期是否延后；第二，交叉比对同适应症竞争药物的安全耐受性与 3/4 级不良反应；第三，查阅美股 10-Q 或港股 18A 财报测算现金储备与潜在配股稀释风险；第四，评估目标市场的商业化推广伙伴与准入报销前景。",
          ],
        },
      ],
      checklist: [
        {
          step: "01",
          title: "原始方案核查",
          action:
            "验证 ClinicalTrials.gov 登记编号（NCT#）、入组患者基线特征及对照组是否采用当下最优标准治疗。",
        },
        {
          step: "02",
          title: "安全性与耐受性穿透",
          action:
            "量化 3/4 级不良事件发生率、致死性不良反应及因毒性停药比例。",
        },
        {
          step: "03",
          title: "商业协议与资产负债表",
          action:
            "审视首付款现金占比、里程碑兑现门槛及净现金支持的季度数，判断增发稀释窗口。",
        },
        {
          step: "04",
          title: "供应链与制造能力",
          action:
            "梳理核心 CDMO 生产商、批次放行周期与监管现场核查（FDA Inspection）历史记录。",
        },
      ],
      references: [
        {
          title: "ClinicalTrials.gov：依沃西单抗对比帕博利珠单抗治疗非小细胞肺癌 III 期研究（HARMONi-2）",
          source: "美国国家医学图书馆",
          type: "临床试验注册数据库",
          citation: "NCT05186974 / 康方生物与 Summit Therapeutics",
          url: "https://clinicaltrials.gov/study/NCT05186974",
        },
        {
          title: "美国 FDA 行业指导原则：抗肿瘤药物与生物制品批准的临床试验终点指南",
          source: "美国食品药品监督管理局 (FDA)",
          type: "监管指导原则",
          citation: "FDA-2018-D-1387 / 肿瘤卓越中心",
          url: "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-trial-endpoints-approval-cancer-drugs-and-biologics",
        },
        {
          title: "中国国家药监局药审中心（CDE）：以临床价值为导向的抗肿瘤药物临床研发指导原则",
          source: "国家药品监督管理局药品审评中心",
          type: "国家监管技术规范",
          citation: "CDE 指导原则 2021年第46号",
          url: "https://www.cde.org.cn",
        },
        {
          title: "《柳叶刀·肿瘤学》（The Lancet Oncology）：标志性头对头肿瘤临床试验疗效与安全性分析",
          source: "The Lancet 出版集团",
          type: "同行评议学术期刊",
          citation: "Lancet Oncol 2024; 25: 1145–1158",
          url: "https://www.thelancet.com/journals/lanonc",
        },
      ],
      actionPrompt:
        "对比康方生物（9926.HK）与信达生物（1801.HK）最新三期临床数据、PFS 风险比、安全性指标及海外 License-out 首付款占比。",
      actionLabel: "在研究工作台中深入探索本课题",
    },
    {
      slug: "ai-chip-cycle",
      number: "02",
      category: "科技 / 供应链",
      concept: "研究思路",
      title: "追踪 AI 芯片周期的连锁反应",
      date: "2026年10月",
      readTime: "阅读时长 7 分钟",
      description:
        "追踪芯片需求、网络设备、制造与客户之间的联系，在形成观点前核对公司财报和产业资料。",
      note: "这是研究方式示例，不构成产业或股票走势预测。",
      abstract:
        "AI 算力周期绝非仅仅是设计芯片与终端营收的简单直线映射。当北美头部云厂商（Hyperscalers）上调百亿美元资本开支时，巨额资金将沿着一条精密的全球网络逐级传导：从尖端光刻与 2.5D/3D 先进封装，到高带宽内存（HBM）、高速光模块、高密度电源转换与冷板液冷散热。本文拆解了研究工作台如何跨越美股、台积电先进制程与 A 股/港股核心供应链，穿透跟踪这轮周期的连锁反应与验证锚点。",
      coreQuestion:
        "云服务巨头每增加 100 亿美元的 AI 资本开支，是如何穿透先进封装产能瓶颈、高速光互连与电力基础设施的？A 股及跨市场核心硬件供应商在哪个环节拥有最强的主导权与业绩弹性？",
      keyQuestions: [
        "台积电 CoWoS 产能月投片量扩张与 HBM3e/HBM4 的良率曲线，如何实质性决定未来 4 至 6 个季度算力加速卡的实际交付节奏？",
        "在集群规模走向 NVL72 及超节点架构时，网络互连价值量为何呈几何级跃升，核心光模块供应商如何维持高毛利率？",
        "A 股硬件领军企业（高速光模块、服务器制造、液冷与电源）如何深度绑定海外云巨头需求，并在国际合规框架下确保持续增长？",
      ],
      keyFindings: [
        {
          title: "先进封装而非晶圆制造已成为核心瓶颈",
          desc: "加速卡的实际出货量受制于台积电 CoWoS-L 月产能与 HBM3e/HBM4 封装良率，构成跟踪季度出货节奏的前瞻先行指标。",
        },
        {
          title: "光互连倍增效应显现（每 GPU 配比达 1:2.5 至 1:4）",
          desc: "从 800G 向 1.6T 光模块升级，配合 DSP 与 LPO 架构，为中际旭创、新易盛等光模块龙头带来极具弹性的经营杠杆。",
        },
        {
          title: "单机柜功率超过 100kW 驱动液冷全面刚性化",
          desc: "从风冷向芯片级冷板式液冷的跨越，使英维克、汇川技术等温控与电源供应商的单柜配套价值量成倍增长。",
        },
      ],
      sections: [
        {
          id: "capex-transmission",
          number: "01",
          tag: "源头需求",
          heading: "源头传导引擎：从云巨头资本开支到算力芯片",
          lead: "算力投资始于云厂商的资产负债表与现金流量表，之后才映射为实体半导体订单。",
          paragraphs: [
            "AI 基础设施周期的最直接驱动力，来自微软、谷歌（Alphabet）、Meta 和亚马逊（AWS）公布的资本开支指引。在每季度的 10-Q 与 10-K 报表中，追踪“购建固定资产所支付的现金（Capex）”能够穿透市场预期，展现真实的数据中心扩建节奏。",
            "然而，巨额资金并非直接等同于瞬时算力。集群部署存在多季度的工程周期。每 100 亿美元的增量资本开支中，通常约 45% 分配给算力加速卡，20% 流向高速网络与光互连，15% 用于电力与温控基础设施，20% 用于土建机房。理解这一分配比例，是寻找二级供应链弹性环节的底层基石。",
          ],
          callout: {
            title: "研究台则",
            content:
              "云厂商的 Capex 口头口径影响市场情绪；现金流量表中的“购建固定资产支付现金”才是验证真实采购的硬指标。",
          },
        },
        {
          id: "packaging-bottlenecks",
          number: "02",
          tag: "物理瓶颈",
          heading: "物理瓶颈点：CoWoS 先进封装、HBM 与载板",
          lead: "算力芯片的交付节奏受制于先进封装产能与高带宽内存的集成瓶颈。",
          paragraphs: [
            "从英伟达 Blackwell 架构到云巨头自研 ASIC（谷歌 TPU、亚马逊 Trainium），前沿算力芯片均为多 Chiplet 模块化系统，高度依赖 2.5D/3D 先进封装。台积电 CoWoS 产能虽从每月约 3.5 万片晶圆向 7 万片以上急速扩充，但高密度中介层（Interposer）与硅通孔（TSV）刻蚀设备依然构成供给天花板。",
            "同时，HBM3e 迈向 HBM4 需要 8 层至 12 层 DRAM 晶圆堆叠并配合微凸块（Microbump）互连，底层基底更将采用台积电 3nm/5nm 先进逻辑制程。SK 海力士、美光与三星的良率竞争直接决定整机柜交付时间表。任何封装良率扰动都会引发上游备货节奏调整，并带动欣兴电子、揖斐电（Ibiden）等高层 ABF 载板需求波动。",
          ],
        },
        {
          id: "optical-and-thermal",
          number: "03",
          tag: "A股杠杆",
          heading: "弹性放大器：A 股光通信、整机代工与液冷温控",
          lead: "网络互连与热密度跨越为大中华区核心硬件龙头带来最丰厚的高经营杠杆。",
          paragraphs: [
            "随着集群从数千卡扩大到 NVL72 机柜架构，算力与网络的配置比例发生巨变。为消除网络延迟导致的 GPU 空转，云巨头大量采购 800G 与 1.6T 光模块。大中华区光通信产业链在全球占据绝对主导地位，中际旭创（300308.SZ）、新易盛（300502.SZ）直接供货北美一线云厂商，天孚通信（300394.SZ）则牢牢掌控光引擎与精密元器件供应。",
            "此外，单机柜功耗突破 100kW 至 130kW 使得传统风冷方案彻底失效。冷板式液冷（包括冷板、冷却液分配单元 CDU、快速接头、歧管）由可选配置转为强制标配。A 股温控龙头如英维克（002837.SZ），结合台达电子、Vertiv 等电力供应巨头，单机柜价值量呈现跳跃式扩容。",
          ],
        },
        {
          id: "domestic-ecosystem",
          number: "04",
          tag: "国内动态",
          heading: "国内算力生态演进与四步验证清单",
          lead: "在出口管制背景下，关注国内自主算力生态与供应链排产的真实节奏。",
          paragraphs: [
            "在申请美国 EAR 出口管制（先进算力与互连带宽限制）背景下，国内算力生态正在加速建立双轨演进格局。以华为昇腾（910B/910C）、寒武纪（688256.SH）、海光信息（688041.SH）为核心的自主生态，正协同长电科技（600584.SH）、通富微电（002156.SZ）等先进封装力量持续突破。",
            "投研人员核实硬件供应链真实景气度时，需紧扣四个步骤：第一，核对头部代工厂（工业富联 601138.SH、立讯精密 002475.SZ）的出货节奏；第二，跟踪原材料采购承诺以防“重复下单（Double-booking）”虚假繁荣；第三，评估北美及国内算力中心电网接入与电力审批排队周期；第四，严密追踪 800G 向 1.6T 产品迭代期的毛利率变动韧性。",
          ],
        },
      ],
      checklist: [
        {
          step: "01",
          title: "资本开支现金流核实",
          action:
            "比对云厂商财报电话会与现金流量表，核实真实硬件支出的季度环比增速。",
        },
        {
          step: "02",
          title: "封装产能节奏跟踪",
          action:
            "锁定台积电季报说明会关于 CoWoS 分配指引与先进制程月投片量披露。",
        },
        {
          step: "03",
          title: "光模块在手订单与海关数据",
          action:
            "交叉核验中际旭创、新易盛的出口交付数据、在手订单及毛利率稳定性。",
        },
        {
          step: "04",
          title: "电力接入与温控部署周期",
          action:
            "追踪目标数据中心供电配额批复进度与机柜液冷 CDU 交付周期。",
        },
      ],
      references: [
        {
          title: "台积电（TSMC）季度法说会报告：先进封装（CoWoS）产能规划与晶圆代工展望",
          source: "台湾积体电路制造 (TSMC)",
          type: "投资者关系披露",
          citation: "TSMC IR Briefing Q3 2026 / CoWoS Roadmap",
          url: "https://investor.tsmc.com",
        },
        {
          title: "TrendForce / Yole Group：AI 服务器供应链与高带宽内存（HBM）深度报告",
          source: "TrendForce / Yole Group",
          type: "半导体产业市场调研",
          citation: "Advanced Packaging Market & Technology Report 2026",
          url: "https://www.trendforce.com",
        },
        {
          title: "美国 SEC 10-K / 10-Q 文件：头部云厂商数据中心资本开支与硬件基础设施披露",
          source: "美国证券交易委员会 (SEC)",
          type: "法定监管报告",
          citation: "Alphabet, Microsoft, Meta Platforms, Nvidia 定期申报",
          url: "https://www.sec.gov/edgar",
        },
        {
          title: "开放计算项目（Open Compute Project, OCP）：高密度 AI 服务器机柜与液冷系统规范",
          source: "Open Compute Project Foundation",
          type: "国际数据中心开放规范",
          citation: "OCP Liquid Cooling Specification v2.4",
          url: "https://www.opencompute.org",
        },
      ],
      actionPrompt:
        "追踪台积电 CoWoS 先进封装产能扩建节奏，并结合中际旭创（300308.SZ）800G/1.6T 光模块订单与英维克（002837.SZ）液冷业务收入占比进行深度拆解。",
      actionLabel: "在研究工作台中深入探索本课题",
    },
  ],
};

export function getJournalArticle(
  slug: string,
  lang: "en" | "zh" = "en"
): JournalArticle | undefined {
  const list = journalArticles[lang] || journalArticles.en;
  return list.find((item) => item.slug === slug);
}
