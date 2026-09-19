# 香港でEC（生鮮食品・定期宅配型D2C）を運営する際の法務・セキュリティ要注意項目レポート

**作成日:** 2026-09-19
**想定読者:** セキュリティ／プライバシー担当、EC事業責任者、法務窓口
**想定事業モデル:** 日本の生鮮食品EC（オイシックス型）が香港消費者向けに越境／現地法人でサービス提供。
会員登録・定期購買（サブスクリプション）・レコメンド・メール／SMS販促・レビュー投稿・クレジットカード決済・冷蔵/冷凍配送を伴う。

---

## 0. 本レポートの出典と限界（先に明記）

本レポートは **DLA Piper "Data Protection Laws of the World" の香港（HONG KONG, SAR）章のカテゴリ構成**
（Law / Definitions / National data protection authority / Registration / Data protection officers /
Collection & processing / Transfer / Security / Breach notification / Enforcement / Electronic marketing / Online privacy）
に沿って整理し、これにEC特有の非プライバシー領域（消費者保護・食品・決済・重要インフラ）を足したものです。

**重要な制約:** 本レポート作成環境では `www.dlapiperdataprotection.com` への直接アクセスが
組織のネットワーク egress ポリシーによって遮断されていた（プロキシが 403 を返却）ため、
同サイト各カテゴリページの記載内容は**検索経由で取得した同サイトの要約**に基づいています。
原文の逐語確認はできていません。

したがって以下の運用ルールを置きます。

- 本レポートは **社内検討用のドラフト**であり、法的助言ではありません。
- **金額・年数・期限・条番号は必ず一次情報（eLegislation, PCPD, CFS, 税関）で確認**してください。本文では確度の低い数値に「※要一次確認」を付しています。
- 最終判断の前に香港法弁護士のレビューを入れてください。

参照した主なURL（各カテゴリの原文）は §10 に一覧化しています。

---

## 1. エグゼクティブサマリ — 最も効く7点

| # | 論点 | なぜ香港特有か | 優先度 |
|---|---|---|---|
| 1 | **ダイレクトマーケティングは刑事罰付き** | PDPO Part 6A。同意なしの販促利用は罰金＋**実刑**があり得る。GDPR型の「行政罰」ではなく刑事事件になる | **最高** |
| 2 | **越境移転は「法律上は自由・実務上はRMC」** | 越境制限の s.33 が**未施行**。禁止はされないが、PCPD推奨モデル条項(RMCs)締結が事実上の標準 | 高 |
| 3 | **漏えい通知は現時点で任意、ただし義務化が予定** | 今は PCPD ガイダンスベース（「実務上可能な限り速やかに」）。義務化＋**課徴金**（HK$10M or 売上10%案）が控える | 高 |
| 4 | **DPP4「all practicable steps」は抽象的＝立証責任が事業者側** | 具体的な技術基準がないため、**業界標準を自分で選んで文書化**しない限り「実務上可能な措置を取った」と言えない | 高 |
| 5 | **委託先（データ処理者）は直接規制されない** | 処理者を縛る手段が**契約しかない**。DPA条項の不備が即データユーザー自身の違反になる | 高 |
| 6 | **定期購買＋生鮮の組合せが消費者保護法に触れやすい** | 商品説明条例(TDO)の「誤認を招く不作為」「おとり広告」「不当な代金受領」は**厳格責任**。欠品・遅延・自動更新が直撃 | 高 |
| 7 | **日本産水産物等の輸入禁止措置が継続中** | 10都県産の水産物・海塩・海藻加工品は輸入・供給が禁止（食品安全命令）。商品マスタ管理が法令遵守の一部になる | **最高** |

---

## 2. 適用法令マップ

| 領域 | 法令・ガイダンス | 監督機関 |
|---|---|---|
| 個人データ | 個人資料（私隠）條例 **Personal Data (Privacy) Ordinance (Cap. 486)**（PDPO）＋6つのデータ保護原則(DPP) | PCPD（Privacy Commissioner for Personal Data） |
| 迷惑電子メッセージ | **Unsolicited Electronic Messages Ordinance (Cap. 593)**（UEMO）＋UEMR＋実務準則 | OFCA / 通訊事務管理局(CA) |
| 消費者保護 | **Trade Descriptions Ordinance (Cap. 362)**（TDO、2013年不公正取引慣行改正）、Sale of Goods Ordinance (Cap. 26)、Unconscionable Contracts Ordinance (Cap. 458)、Supply of Services (Implied Terms) Ordinance (Cap. 457) | 香港税関(C&ED)、消費者委員会 |
| 電子取引 | **Electronic Transactions Ordinance (Cap. 553)** | ー |
| 食品 | **Food Safety Ordinance (Cap. 612)**（輸入業者/販売業者登録・記録保持）、Public Health and Municipal Services Ordinance (Cap. 132) Part V、食品表示・栄養表示規則、日本産食品に関する食品安全命令 | FEHD / **食物安全中心 (CFS)** |
| サイバーセキュリティ | **Protection of Critical Infrastructures (Computer Systems) Ordinance (Cap. 653)**（2026/1/1施行）＋実務準則、Crimes Ordinance の不正アクセス関連 | 重要インフラ（電脳系統安全）専員辦公室、警察 |
| 決済 | Payment Systems and Stored Value Facilities Ordinance (Cap. 584)（自社プリペイド/ポイントを発行する場合）、PCI DSS（契約上の要求） | HKMA、カードブランド |
| AI利用 | PCPD「AI: Model Personal Data Protection Framework」(2024/6)、従業員向け生成AI利用ガイドラインのチェックリスト(2025/3) | PCPD |

---

## 3. DLA Piper カテゴリ別の整理（香港の規律 → ECでの論点 → 実務対応）

### 3.1 Law（根拠法）

- 個人データの収集・取扱いを規律するのは **PDPO (Cap. 486)**。**1996年施行**、**2012/2013年に大幅改正**（特にダイレクトマーケティング規制の導入）、**2021年改正**で「doxxing（個人情報晒し）」の刑事化と PCPD の執行権限強化。
- GDPR のような包括的単一法ではなく、**6つのデータ保護原則（DPP1〜DPP6）＋個別条文**という構成。

**ECでの論点:** 「香港版GDPR」として社内展開すると過剰にも過小にもなる。特にマーケティングは香港が**より厳しい**（刑事罰）、越境移転は**より緩い**（s.33未施行）という非対称を理解する必要がある。

### 3.2 Definitions（定義）

| 概念 | 香港の扱い | 実務インパクト |
|---|---|---|
| Personal data | 生存する個人に関する情報で、個人を特定でき、**アクセス／処理が実務上可能な形式**であるもの | ログ・Cookie ID・端末IDも、会員IDと突合可能なら該当し得る |
| Data user | 個人データの収集・保有・処理・利用を**コントロールする者** | EC運営者本体。「コントロール」が判断軸 |
| Data processor | データユーザーのために処理する者。**PDPOで直接規制されない** | 3PL・CRM・クラウド・広告代理店の統制は**契約と監査でしか担保できない** |
| Sensitive personal data | **特別カテゴリの概念なし**。ただし PCPD の非拘束ガイダンス（生体情報等）は「より機微なデータには高い水準を」と示唆 | 食物アレルギー情報・健康志向データは「法律上は通常データ、実務上は要配慮」として扱うのが安全 |

**ECでの論点（重要）:** 生鮮食品ECは **アレルギー・既往症・妊娠/育児ステージ・宗教的食制限**といった、
GDPRなら特別カテゴリに該当する情報を「ふつうの注文属性」として収集しがちです。
香港法上は特別扱いがなくても、**漏えい時の被害（real risk of significant harm）認定と評判被害は健康データ並み**になります。
→ 社内データ分類で **S1（機微相当）** を独自に設け、暗号化・アクセス最小化・保持期間短縮を適用すること。

### 3.3 National data protection authority（監督機関）

- **PCPD（個人資料私隠專員公署）**。PDPO の執行、調査、執行通知（enforcement notice）発出、苦情処理、ガイダンス発行、コンプライアンスチェックを担う。
- 現時点で**行政罰（課徴金）を直接課す権限はない**。執行通知→不遵守が刑事罰、という二段構え。
- 2021年改正以降、doxxing について強力に執行している。
  参考実績（2021/10/8〜2024/8/31）: 刑事捜査 **363件**、**59名逮捕**（58事案）、46プラットフォームへ **2,000件超**の停止通知、
  約 **33,500件**の doxxing 投稿削除要請、遵守率 **96%超**。

**ECでの論点:** 商品レビュー・Q&A・コミュニティ機能を持つECは、**第三者の個人情報を晒す投稿の置き場**になり得ます。
PCPD から停止通知（cessation notice）が来た場合、**削除の実行体制と記録**が必要。
→ UGC のモデレーション SLA、法務エスカレーション経路、削除ログの保全を設計しておくこと。

### 3.4 Registration（登録）

- **個人データ取扱いに関する一般的な登録・届出義務はない**（データベース登録制度なし）。

**ECでの論点:** プライバシー面での「登録」は不要な一方、**事業としての登録は別途必要**です。
香港法人設立（Companies Ordinance）／Business Registration、および食品を扱うなら
**食品輸入業者・食品販売業者としての FEHD 登録**（§4.3）。ここを混同しないこと。

### 3.5 Data protection officers（DPO）

- **DPO の選任義務はない**。香港居住者要件もなく、選任しないこと自体への罰則もない。
- ただし PCPD は **Privacy Management Programme（PMP）ベストプラクティスガイド**（2014年2月発行、2019年3月改訂）で、
  PDPO遵守を監督する**責任者の指名**とPMPの整備を推奨。

**ECでの論点:** 義務がないことは「置かなくてよい」を意味しません。
執行通知が出た場面や漏えい対応で、**PMPの存在とオーナーシップの所在**が「practicable steps を尽くしたか」の評価に直結します。
→ 最小構成でも「Privacy Owner（役員級）＋実務担当＋四半期レビュー＋データインベントリ」を文書化。

### 3.6 Collection & processing（収集・利用）

中核は6つの **DPP**。EC文脈に落とすと次の通り。

| DPP | 要旨 | 生鮮EC での具体論点 |
|---|---|---|
| **DPP1** 目的・収集方法 | 適法・公正な手段で、**目的に必要かつ過剰でない**範囲で収集。収集時（または直前）に目的・移転先の種類・アクセス/訂正請求の連絡先を告知（**PICS**: Personal Information Collection Statement） | 会員登録フォームでの「生年月日」「性別」「家族構成」「勤務先」は本当に必要か。アレルギー欄は任意化し用途を限定。PICS を登録画面・決済画面・アプリ初回起動で提示 |
| **DPP2** 正確性・保持 | 正確に保ち、**必要期間を超えて保持しない** | 退会後の注文履歴・配送先・カードトークンの保持期間を定義（会計/税務要件と整合）。改正案では**保持期間ポリシーの策定が義務化**される方向 |
| **DPP3** 利用制限 | **収集時の目的または直接関連する目的**にのみ利用。それ以外は **prescribed consent**（明示・自発的かつ撤回されていない同意）が必要 | ここが最大の落とし穴。「配送のために取得した住所」を**レコメンド学習・ルックアライク広告・提携先送客**に回すのは目的外になり得る。**目的の粒度設計**が生命線 |
| **DPP4** セキュリティ | 不正・偶発的なアクセス／処理／消去／喪失／利用に対し、データの性質等を踏まえ**実務上可能なすべての措置**。処理者利用時は**契約その他の手段**で同等の保護と保持期間制限を確保 | §3.8・§5 で詳述 |
| **DPP5** 透明性 | ポリシー・実務を一般に入手可能に（**PPS**: Privacy Policy Statement） | PICS（収集時告知）と PPS（一般公表ポリシー）は**別物**。香港サイトは両方置くのが標準 |
| **DPP6** 開示・訂正請求 | 本人のアクセス請求(DAR)・訂正請求に応じる。**原則40日以内**に対応、手数料は「過大でない」範囲 ※要一次確認 | DAR対応の SLA・本人確認手順・回答テンプレを用意。データがCRM/WMS/BI/広告基盤に散っていると40日は容易に破綻する |

**同意の取り方（実装指針）**
- 香港は「オプトアウト前提の黙示同意」では足りない場面（特にマーケティング、§3.11）がある。
- **Cookie バナーの同意は PDPO の prescribed consent とイコールではない**。用途別に分離した同意記録（同意文言のバージョン、取得日時、UI スクリーンショット）を残すこと。
- 口頭同意を得た場合、**14日以内に本人の書面確認**を得る運用が求められる場面がある ※要一次確認。コールセンター運用に影響。

### 3.7 Transfer（越境移転）

- **越境移転の制限は現在存在しない**。PDPO **s.33**（香港外への移転を原則禁止し、一定条件下でのみ許容）は**留保され未施行**。
- ただし PCPD の非拘束ガイダンスは s.33 の遵守を推奨。s.33 の条件は
  ①移転先が **ホワイトリスト**掲載地域、②本人の**個別かつ自発的な同意**、③**執行可能なデータ移転契約**（PCPD が推奨モデル条項 **RMCs** を公表）。
- 実務では、越境移転前に **RMCs を海外受領者と締結**するのが一般的。

**ECでの論点（日本企業として最重要）:**
香港会員のデータを**日本本社のCRM/DWH**、**日本のクラウドリージョン**、**中国本土のBPO/工場**に流す構成は典型的に発生します。

| 移転先 | 香港側の扱い | 追加で効いてくる規制 |
|---|---|---|
| 日本（本社・AWS/GCP東京） | s.33未施行なので香港法上は禁止されない。RMCs締結が推奨 | 日本の個情法（委託/共同利用の整理） |
| 中国本土（BPO・製造委託） | 同上 | **PIPL / データ出境**。中国側に入った後の再移転・安全評価が別問題として発生。香港→本土は「越境」として扱われる |
| 米国SaaS（CRM, MA, 分析） | 同上 | 各SaaSのDPA。サブプロセッサ連鎖の可視化 |

→ 「香港は緩いから何もしなくてよい」ではなく、**RMCs（または同等のDPA条項）を全ベンダーに横展開**し、
移転先・データ項目・法的根拠を **移転レジスタ（RoPA相当）** として一覧化してください。s.33 が将来施行された場合の移行コストを最小化できます。

### 3.8 Security（セキュリティ）

- **DPP4**: データユーザーは、データの**性質**、漏えい時の**害の程度**、**保管場所**、**伝送手段**、**アクセス制御**等を考慮し、
  不正または偶発的なアクセス・処理・消去・喪失・利用から個人データを保護するため、**実務上可能なすべての措置**を講じなければならない。
- **処理者（委託先）を使う場合**、データユーザーは**契約その他の手段**により
  ①不正／偶発的なアクセス・処理・消去・喪失・利用の防止、②**必要期間を超える保持の防止**を確保しなければならない。

**「all practicable steps」への対処法:**
条文は技術要件を列挙しません。よって**自らベースラインを選定して適用・証跡化する**ことが防御になります。推奨は次のマッピング。

| 領域 | 最低限やること | 証跡 |
|---|---|---|
| ID／認証 | 会員：パスワードレスまたは強度要件＋**クレデンシャルスタッフィング対策**（レート制限、パスワードリスト照合、異常ログイン検知）／管理者：**MFA必須**、特権はJIT付与 | 設定エクスポート、ブロック統計 |
| 暗号化 | 全通信TLS1.2+／DB・バックアップの保存時暗号化／カード情報は**自社非保持（トークナイゼーション）** | 構成管理、PCI SAQ |
| アクセス制御 | 会員PII・アレルギー情報は**最小権限＋職務分離**、本番データのステージング持ち出し禁止、マスキング | 権限棚卸記録（四半期） |
| ログ／監視 | 認証・権限変更・PII大量参照・エクスポート操作の監査ログを**改ざん耐性のある領域**に保持。アラート閾値を定義 | SIEMルール、保持期間設定 |
| 脆弱性管理 | 資産インベントリ、定期スキャン、**年次ペネトレーションテスト**、SLA付きパッチ運用 | スキャン結果・是正記録 |
| 委託先管理 | ベンダーリスク評価、DPA（RMC相当条項）、**サブプロセッサ承認**、退出時のデータ返却・削除証明 | 契約書、削除証明書 |
| 開発 | SAST/DAST、シークレット検出、IaC設定監査、**本番アクセスの承認フロー** | CIログ、レビュー記録 |
| 教育 | 全社年次＋CS/物流の実務別トレーニング、フィッシング演習 | 受講記録 |

**生鮮EC特有の脅威シナリオ（脅威モデリングの起点）**

1. **クレデンシャルスタッフィング → 定期便の配送先改変／ポイント窃取。** 被害が「食品の横取り」という物理的形になるため苦情化しやすい。
2. **カード不正利用（CNP）** と、それに対抗するための不正検知データ収集が **DPP1の「過剰でない」** と衝突する。目的と保持期間を明記して整合させる。
3. **配送業者/3PL の侵害 → 住所・在宅時間帯・不在情報の漏えい。** 住宅への物理リスクに直結。処理者契約とインシデント連絡SLAが要。
4. **スクレイピング／ボット転売**（限定品・キャンペーン枠）。対策で取得する端末フィンガープリントも個人データ足り得る点に注意。
5. **内部不正**：CS担当による会員情報の閲覧・持ち出し。大量参照検知が最も効く。
6. **レコメンド／MAツール連携時の目的外利用**（技術ではなく統制の失敗。§3.6 DPP3）。
7. **サードパーティスクリプト（タグ）経由の情報流出**（決済ページのスキミング）。CSP と タグ管理の承認フロー。

### 3.9 Breach notification（漏えい通知）

- **現行法上、当局または本人への通知義務はない**（mandatory notification なし）。
- 「データ侵害」の**法定定義もない**。PCPD の非拘束ガイダンスでは
  「データユーザーが保有する個人データのデータセキュリティの侵害の疑いで、**不正または偶発的なアクセス・処理・消去・喪失・利用のリスクにデータを晒すもの**」と定義。
- PCPD は**ベストプラクティスとして通知を推奨**。
  **Guidance on Data Breach Handling and Data Breach Notifications（2023年6月改訂版）**では、
  - 内部調査の進捗を待たず、**認識後「実務上可能な限り速やかに（as soon as practicable）」** PCPD と影響を受けた本人へ通知すべき
  - 特に **本人に現実的な重大な害（real risk of harm）が生じるおそれ**がある場合
  - 本人への通知手段は電話・書面・メール・対面。直接通知が実務上困難な場合は**公表・新聞広告・ウェブ／SNS告知**
  - PCPD は **2023年6月に e-Data Breach Notification Form** を提供。**口頭通知は受理されない**
- **義務化が予定**：政府/PCPDの改正提案には**強制的な漏えい通知**、**データ処理者の直接規制**、**保持期間ポリシーの義務化**、
  **行政罰（課徴金）**（HK$10Mまたは年間売上の10%のいずれか高い額という案）が含まれる ※法案の成立状況は要一次確認。

**ECでの論点:** 「香港は通知義務がないから様子見」という判断は最悪手です。理由は3つ。
(1) 通知しない判断も **DPP4遵守の一部として事後評価**される、
(2) EC会員は多国籍で、**日本の個情法（速報3〜5日目安・確報30日/60日）やGDPRの72時間**が同時に走る、
(3) 義務化が来た時にプレイブックがないと初動で破綻する。
→ **最も厳しい法域に合わせた単一プレイブック**（§6）を用意し、香港はその一分岐として扱うのが正解。

### 3.10 Enforcement（執行・制裁）

| 手段 | 内容 | 制裁 |
|---|---|---|
| 執行通知（enforcement notice） | PCPD が DPP 違反の是正を命令 | **不遵守は刑事犯**。罰金最大 **HK$50,000** ＋ 拘禁 **最長2年**、継続する場合 1日あたり **HK$1,000** ※要一次確認 |
| 反復違反 | 同種文脈での再度の有罪判決 | **レベル6の罰金（HK$100,000）** ＋ 拘禁2年 ※要一次確認 |
| ダイレクトマーケティング違反 | 執行通知を経ずに**直接刑事犯**となる類型 | 態様により **最大HK$500,000＋3年**（同意なき利用）〜 **最大HK$1,000,000＋5年**（第三者提供等） ※要一次確認 |
| 民事 | 違反により損害を受けた本人は**損害賠償請求**が可能。PCPD は本人の訴訟支援スキームを運営 | 賠償額＋レピュテーション |
| （提案中） | 行政罰（売上連動の課徴金） | 現行より**大幅に高額化**する見込み |

**ECでの論点:** 香港の特徴は **「役員が刑事責任の射程に入る」**点です。
GDPR型の「会社が罰金を払う」リスク前提で作られた社内規程は、香港では**エスカレーション基準が甘すぎる**ことがあります。
→ マーケティング施策のリリース前チェックを**法務の必須ゲート**にし、承認記録を残してください（後述チェックリスト §8.2）。

### 3.11 Electronic marketing（電子マーケティング）— **最重要**

香港は **2階建て**の規制です。両方に同時に適合する必要があります。

**(A) PDPO Part 6A（個人データを使った「ダイレクトマーケティング」）**

- **ダイレクトマーケティングの定義**: 商品・施設・サービスの提供または提供可能性の広告、あるいは慈善・文化・慈善事業・娯楽・政治その他の目的での寄付・拠出の勧誘であって、
  郵便・ファクシミリ・電子メール・電話などの**直接的手段で特定の者に対して**行われるもの。
- 主な義務（実装レベル）:
  1. 初めて個人データをダイレクトマーケティングに使う前に、**その意図を本人に通知**し、対象となるデータの種類と販促するクラス（商品/サービスの種類）を明示。
  2. **応答チャネル（response channel）** を提供し、本人が無償で不同意を伝えられるようにする。
  3. 本人が同意（または不異議の表明）した後でなければ利用できない。
  4. **第三者に個人データをダイレクトマーケティング目的で提供**する場合は、より重い要件（**書面による同意**、提供先のクラスの明示等）。
  5. 本人からの**中止要求（opt-out）には応じる義務**。
  6. 口頭同意の場合、**14日以内に書面確認**を得る運用 ※要一次確認。
- **罰則**: 同意なき利用は最大 **HK$500,000 ＋ 拘禁3年**、第三者提供を伴う類型は最大 **HK$1,000,000 ＋ 拘禁5年** ※要一次確認。
- PCPD の **Guidance on Direct Marketing（2023年4月版）** が具体的な文例・運用を示しています。

**(B) UEMO (Cap. 593)（「商業電子メッセージ」＝CEM の送信ルール）**

- 対象は **香港とのリンク(Hong Kong link)** を持つ CEM（メール、SMS、ファクシミリ、事前録音音声等）。
- 主な義務（UEMR＋実務準則が詳細を規定）:
  - **正確で明瞭な送信者情報（sender information）** の記載
  - **配信停止設備（unsubscribe facility）** と **配信停止に関する記述（unsubscribe facility statement）** の記載
  - 送信者情報と配信停止記述を**メッセージ冒頭に所定の順序で提示**（ファクシミリ／メールでは1ページ目の上部または下部に、フォントサイズ・位置・コントラストの点で**合理的に視認可能**に）
  - 配信停止要求の**期限内の反映**（一定営業日内）※要一次確認
  - **Do-Not-Call (DNC) 登録簿**の尊重。DNC は **ファクシミリ・ショートメッセージ・事前録音電話メッセージ**の3種について維持されている
    （＝**電子メールはDNC登録簿の対象外**だが、上記の記載義務と配信停止義務は適用）
  - 誤認を招く件名、アドレス収集ソフトの使用等の禁止
- **罰則**: 違反は罰則対象（初回有罪でレベル6相当、再犯で加重。詐欺的態様はより重い） ※要一次確認。

**ECでの実装インパクト（最も手戻りが多い箇所）**

| よくある実装 | 香港でのリスク | 直し方 |
|---|---|---|
| 会員登録時に「規約とプライバシーポリシーに同意」チェック1個で販促も包含 | Part 6A の**通知＋応答チャネル＋同意**要件を満たさない可能性が高い | **販促用途の同意をチェックボックスとして分離**し、チャネル別（メール/SMS/電話/郵便）・カテゴリ別に取得 |
| 提携先（産地・メーカー・決済事業者）へのリード共有 | 第三者提供＝**書面同意**が必要な重い類型。最大HK$1Mの射程 | 原則停止。必要なら**独立した書面同意フロー**を設計し、提供先クラスを明示 |
| キャンペーンSMS一斉送信 | DNC登録簿の確認漏れ＋送信者情報／配信停止記述の欠落 | 送信前に**DNC照合をパイプラインに組み込む**。テンプレートに必須要素をハードコード |
| 配信停止が「次回配信から」反映 | 期限超過の配信＝違反 | 配信停止を**即時・全チャネル横断**で反映（サプレッションリストの中央化） |
| A/Bテストでテンプレートを差し替え | 必須記載が欠落したバリアントが本番に出る | **必須要素のリンター**をCIに入れ、欠落したテンプレはデプロイ不可にする |

> セキュリティ担当としての実務的な提案：**「同意状態」と「サプレッション」を、認証や権限と同格の統制対象**として扱ってください。
> 同意レコードの改ざん・欠損は、そのまま刑事リスクに翻訳されます。監査ログ、変更履歴、バックアップ、削除不可設定を適用する価値があります。

### 3.12 Online privacy（オンラインプライバシー／Cookie）

- **Cookie 専用法はない**。PDPO の原則がオンライン環境にそのまま適用される。
- データユーザーは**インターネット経由で個人データを収集する目的を本人に通知**する義務を負う。
- **Cookie で訪問者の個人データを収集する場合はその旨を知らせるべき**であり、
  さらに **Cookie を受け入れない場合にサイト機能に影響が出るかどうかも知らせるべき**。
- PCPD はオンライン行動ターゲティング等についてもガイダンスを公表。

**ECでの論点:**
- GDPR型の「同意なしに非必須Cookieを置かない」までは要求されていないが、**通知の具体性**（どのCookieが何を収集し、拒否したら何が壊れるか）が求められる。
- したがって **Cookie インベントリとカテゴリ分類が実質的な必須作業**。タグマネージャに野良タグが入る運用は不適合になりやすい。
- アプリの場合は **端末ID・位置情報・通知トークン**を同じ枠組みで扱う。
- 決済ページに広告/分析タグを載せない（スキミング対策＋目的外収集回避）。

---

## 4. EC特有の追加論点（PDPO以外）— ここを落とすと事業が止まる

### 4.1 消費者保護：TDO の不公正取引慣行（厳格責任）

2013年7月19日施行の改正で、**6類型の不公正取引慣行**が犯罪化されました。
サービスに関する虚偽表示、**誤認を招く不作為（misleading omissions）**、
**攻撃的な商慣行（aggressive commercial practices）**、**おとり広告（bait advertising）**、
**bait-and-switch**、**不当な代金受領（wrongly accepting payment）**。
bait-and-switch（故意の立証が必要）を除き、**厳格責任**です。
また、越境取引の増加を踏まえた**回避防止規定**があり、香港のトレーダーは**香港外の消費者に向けた商慣行**についても罪に問われ得ます。
執行は**香港税関**が中心（一定分野で通訊事務管理局が並行管轄）。

**生鮮・定期購買での具体リスク:**

| 慣行 | 抵触しやすい類型 | 対策 |
|---|---|---|
| 「毎週お届け」と表示しつつ天候・欠品で代替品送付 | 誤認を招く不作為、虚偽表示 | 代替品ポリシーを**購入前**に明示。代替率の実績を管理 |
| 初回割引→自動更新で通常価格 | 誤認を招く不作為 | 更新時期・更新後価格・解約方法を**申込画面と確認メールに明記**。事前リマインド |
| 在庫がない商品の掲載・受注 | **おとり広告／不当な代金受領** | リアルタイム在庫連動。決済**オーソリと確定のタイミング分離**、欠品時の即時返金 |
| 解約導線が電話のみ・引き留めが執拗 | **攻撃的な商慣行** | オンライン解約を同等の容易さで提供。引き留めスクリプトのレビュー |
| 「産地直送」「オーガニック」等の訴求 | 虚偽表示 | 証跡（認証書・産地証明）の保管。表現の法務レビュー |
| レビューの操作・自社スタッフ投稿 | 虚偽表示 | UGCポリシー、インセンティブ付きレビューの開示 |

※関連：Sale of Goods Ordinance（品質・目的適合性の黙示条件）、Unconscionable Contracts Ordinance（消費者契約の不当条項）、
Supply of Services (Implied Terms) Ordinance。**Electronic Transactions Ordinance (Cap. 553)** により電子契約・電子記録の法的効力は基本的に認められる。

### 4.2 決済

- カード情報は**自社で保持しない**設計（PSPのホステッドフィールド／トークナイゼーション）。PCI DSS の適用範囲を最小化。
- 自社プリペイド残高・チャージ式ポイントを発行する場合、**Payment Systems and Stored Value Facilities Ordinance (Cap. 584)** の
  **SVFライセンス**該当性を必ず検討（該当すると規制コストが跳ね上がる）。
- 3Dセキュア／不正検知の導入と、そこで収集するシグナルの **DPP1（過剰でない）／DPP3（目的）** 整合。

### 4.3 食品（生鮮EC の中核リスク）

- **Food Safety Ordinance (Cap. 612)**:
  - **食品輸入業者・食品販売業者（wholesale供給）の登録制度**。FEHD（食物環境衞生署長）への登録が必要で、
    申請時に**取り扱う主要な食品カテゴリと分類を特定**する。
  - **食品の移動に関する記録保持義務（トレーサビリティ）**。
- **高リスク食品は事前許可／個別の行政手続が必要**：
  **(a) 猟鳥獣肉・食肉・家禽肉、(b) 牛乳および乳飲料、(c) 冷菓、(d) 水産物**。
  これ以外の食品の輸入には原則として事前許可は不要。
- **Public Health and Municipal Services Ordinance (Cap. 132) Part V**：
  s.54 により**販売用食品は人の消費に適さないものであってはならない**。食品表示・栄養表示規則も同条例の下。
- **日本産食品に関する輸入規制（2026年時点で継続中）**:
  **2023年8月24日**以降、**東京・福島・茨城・宮城・千葉・群馬・栃木・新潟・長野・埼玉の10都県**を原産地とする
  **水産物・海塩・海藻加工品**の香港への輸入および供給が**食品安全命令により禁止**されています。
  禁止対象外の日本産水産物等についても、CFS が輸入前に**放射能検査**（Codex のガイドライン値基準）を実施。
  CFS の公表によれば、**2026年4月21日時点で輸入業者による違反の疑い事案は累計51件**にのぼり、執行は継続中。

**これはセキュリティ／データ品質の問題でもある:**
「どの商品が、どの都県の、どの加工場由来か」を**商品マスタの属性として正確に保持し、出荷ブロックに機械的に反映**できなければ、
人的ミスで**刑事リスクのある出荷**が起きます。

→ 推奨統制：
1. 商品マスタに **原産地（都道府県粒度）・カテゴリ（水産物/海塩/海藻加工品の別）・加工地** を必須項目化。
2. **禁止リストを設定ファイルではなくルールエンジン**として実装し、受注・出荷・カタログ公開の3点でブロック。
3. 禁止リストの更新を**変更管理プロセス**に載せる（CFS 公表監視 → 承認 → 反映 → 反映証跡）。
4. 冷蔵/冷凍の**温度記録（IoT）の保全**：改ざん耐性とトレーサビリティ記録要件への対応。

### 4.4 サイバーセキュリティ法：Cap. 653（2026/1/1施行）

- **Protection of Critical Infrastructures (Computer Systems) Ordinance (Cap. 653)** が **2026年1月1日**に施行。
  同日、重要インフラ（電脳系統安全）専員辦公室が**実務準則（Code of Practice）**を発出。
- 指定された **CI事業者（CIO）** の主な義務：
  **香港内に事務所を維持**、**専門のコンピュータシステム・セキュリティ管理部門の設置**、
  **セキュリティ管理計画の提出と実施**、**定期的なリスク評価と監査**、**インシデントの報告と対応**。

**ECでの論点:** 一般的な食品小売ECは通常 CIO 指定の対象ではありません。ただし、
(1) 対象8セクター（エネルギー、通信、金融、航空、陸上/海上運輸、医療等）**への供給・連携**がある場合、
(2) 指定された物流/決済/通信事業者と密結合している場合、
**契約経由で同水準の統制を要求される**可能性があります。
→ 主要パートナーの CIO 指定状況を確認し、**インシデント報告SLAを契約に織り込む**。自社の SMP（セキュリティ管理計画）を
Cap.653 の実務準則の構成に寄せておくと、将来の要求に低コストで応答できます。

### 4.5 AI（レコメンド・チャットボット・需要予測）

- PCPD **「Artificial Intelligence: Model Personal Data Protection Framework」**（2024年6月11日公表）。
  AIシステムを**調達・導入・利用**する組織向けの初のガイダンスで、PDPO遵守の観点から
  AIガバナンス戦略、リスクベースのアセスメント、システム実装・管理、ステークホルダーとのコミュニケーションを扱う。
- PCPD **従業員による生成AI利用に関する内部ガイドライン作成チェックリスト**（2025年3月31日公表）。
  推奨される記載事項：**許容される利用範囲**、**入力してよい情報の種類に関する明確な指示**、
  **出力情報の許容される利用目的**、**適用されるデータ保持ポリシー**。

**ECでの論点:** 「おすすめ献立」「アレルギー配慮レコメンド」「CSチャットボット」は
**DPP1（過剰でない収集）・DPP3（目的外利用）・DPP4（セキュリティ）** が同時に問題になる領域です。
また、CS担当が会員の問い合わせ文面を外部LLMに貼るのは典型的な情報漏えい経路です。
→ 生成AI利用ポリシー（禁止データ、承認ツール、ログ保持）を PCPD チェックリストの構成に合わせて整備。
プロンプトインジェクションや機密漏えいの耐性検証は、本リポジトリ（J-ART）のような**敵対的評価ハーネス**で継続的に測るのが合理的です。

---

## 5. セキュリティ管理策の優先実装リスト（DPP4を「立証可能」にする）

| 優先 | 施策 | 根拠 | 完了の定義 |
|---|---|---|---|
| P0 | 会員認証のクレデンシャルスタッフィング対策（レート制限・漏えいパスワード照合・異常検知） | DPP4 | ブロック率・検知アラートのダッシュボード |
| P0 | 管理者・CS・3PL連携アカウントの **MFA必須化**、特権の棚卸 | DPP4 | 全特権アカウントのMFA率100%の証跡 |
| P0 | カード情報の自社非保持化（トークナイゼーション） | DPP4/PCI | SAQ区分の確定 |
| P0 | マーケティング同意・サプレッションの中央管理＋監査ログ | Part 6A / UEMO | 同意レコードの改ざん検知、即時反映の測定 |
| P0 | 日本産水産物等の**禁止原産地ブロック**をルールエンジン化 | 食品安全命令 | 受注/出荷/公開の3点でのブロックテスト合格 |
| P1 | データインベントリ＋移転レジスタ（移転先・項目・根拠・RMC締結状況） | DPP1/DPP3/s.33対応準備 | 全ベンダーの棚卸完了 |
| P1 | 全委託先とのDPA更新（RMC相当条項・保持期間・サブプロセッサ承認・削除証明） | DPP4（処理者は契約でしか縛れない） | 契約カバレッジ100% |
| P1 | PII大量参照・エクスポートの検知アラート（内部不正対策） | DPP4 | ルール稼働とレビュー記録 |
| P1 | 保持期間ポリシーの策定と自動削除ジョブ | DPP2（＋義務化予定） | データ種別ごとの保持年数と削除実績 |
| P1 | インシデント対応プレイブック（香港＋日本＋EU分岐）＋年1回の机上演習 | 通知ガイダンス／義務化予定 | 演習記録と改善課題のクローズ |
| P2 | Cookie／タグのインベントリとCSP、決済ページのタグ排除 | Online privacy / スキミング対策 | 野良タグ0件の継続監視 |
| P2 | 年次ペネトレーションテスト、SAST/DAST/シークレット検出のCI統合 | DPP4 | 是正SLA達成率 |
| P2 | 生成AI利用ポリシー＋レコメンド/チャットボットの敵対的評価 | PCPD AIフレームワーク | ポリシー公開、評価レポート |
| P2 | UGC（レビュー）の doxxing 対応フロー（PCPD停止通知対応） | 2021年改正 | 削除SLAと記録 |

---

## 6. インシデント対応プレイブック（香港分岐）

香港に通知義務がない現状でも、**多法域共通の単一プレイブック**を持ち、香港をその分岐として扱います。

```
[検知] → [初動封じ込め] → [トリアージ:個人データ該当性・件数・機微度] 
   ├─ 香港 : real risk of significant harm の評価
   │         → 「実務上可能な限り速やかに」PCPD へ **e-Data Breach Notification Form** で通知（口頭は不可）
   │         → 本人へ 電話/書面/メール/対面。直接通知が困難なら 公表・広告・Web/SNS 告知
   │         → 内部調査の完了を待たない（進捗中でも通知する）
   ├─ 日本 : 個情法 委員会報告（速報／確報）＋本人通知
   ├─ EU/UK: GDPR 72時間（該当する場合）
   └─ カード: PCI / カードブランド・PSP への報告
→ [是正] → [再発防止] → [記録保全（判断根拠を含む）] → [事後レビュー]
```

**必ず記録に残すもの（後の DPP4 評価に直結）:** 検知時刻、判断者、通知可否の判断根拠、
通知しなかった場合の理由、封じ込め措置、影響範囲の算定方法。

**事前に用意しておくもの:** PCPD 提出フォームの記入テンプレ、本人向け通知文（繁体字中文・英語・日本語）、
Webサイト告知の掲載手順、CS想定問答、3PL/PSP の緊急連絡先と報告SLA。

---

## 7. リスク登録簿（抜粋・優先度付き）

| ID | リスク | 影響 | 主な統制 | 残余リスク評価の観点 |
|---|---|---|---|---|
| HK-01 | 販促同意の不備で Part 6A 違反 | **刑事罰（役員リスク）**・事業停止級のレピュテーション | 同意分離、DNC照合、テンプレリンター、法務ゲート | 同意レコードの完全性を監査できるか |
| HK-02 | 日本産禁止品目の出荷 | 刑事/行政処分、商品回収、輸入停止 | 原産地マスタ、ルールエンジン、変更管理 | 手動例外処理の有無 |
| HK-03 | 委託先（3PL/CRM）経由の漏えい | DPP4違反、住所情報の物理リスク | DPA、ベンダー評価、報告SLA | サブプロセッサの可視性 |
| HK-04 | クレデンシャルスタッフィング／アカウント乗っ取り | 金銭被害＋苦情＋PCPD調査 | MFA、異常検知、漏えいPW照合 | 会員側MFAの普及率 |
| HK-05 | 定期購買の自動更新・解約導線でTDO抵触 | 税関の執行、返金対応 | 事前開示、オンライン解約、リマインド | 実装と表示文言の乖離 |
| HK-06 | 目的外のデータ利用（広告・提携送客） | DPP3違反、第三者提供は重い類型 | 目的の粒度設計、データ利用申請フロー | 分析基盤での再利用の統制 |
| HK-07 | 漏えい初動の遅延 | 義務化後は課徴金、現状も DPP4 評価に影響 | プレイブック、演習、e-Formテンプレ | 24時間内にトリアージ完了できるか |
| HK-08 | レビュー欄での doxxing 放置 | PCPD停止通知、刑事捜査の関与 | モデレーション、削除SLA、記録 | 通報から削除までの実測時間 |
| HK-09 | s.33（越境制限）の将来施行 | 既存のデータフローが不適合化 | RMCs 先行締結、移転レジスタ | 移転先の集約度 |
| HK-10 | Cap.653 由来の契約要求 | パートナー要件を満たせず取引条件悪化 | SMPを実務準則の構成に整合 | 主要パートナーのCIO指定状況 |

---

## 8. チェックリスト

### 8.1 サイト／アプリ公開前（プライバシー）
- [ ] **PICS**（収集時告知）を 会員登録・決済・アプリ初回起動 に設置し、目的・移転先の種類・アクセス/訂正の連絡先を記載
- [ ] **PPS**（プライバシーポリシー）を公表（PICSとは別に）
- [ ] 収集項目の棚卸：各項目に「目的」「必要性の根拠」「保持期間」を紐付け（DPP1/DPP2）
- [ ] アレルギー・健康志向等を **S1（機微相当）** に分類し、暗号化・権限最小化を適用
- [ ] Cookie／タグのインベントリと、**拒否時の機能影響**の記載
- [ ] **アクセス請求（DAR）対応手順**（本人確認・40日SLA・手数料方針）※期限は要一次確認
- [ ] 保持期間ポリシーと自動削除ジョブ
- [ ] 繁体字中文と英語での提供（日本語のみは不適切）

### 8.2 マーケティング施策リリース前（法務必須ゲート）
- [ ] 販促利用の**同意**が、チャネル別（メール/SMS/電話/郵便）・カテゴリ別に取得されているか
- [ ] 初回利用前の**意図の通知**と**応答チャネル**の提供が済んでいるか
- [ ] 第三者提供を含まないか。含む場合は**書面同意**と提供先クラスの明示があるか
- [ ] メッセージに **送信者情報** と **配信停止設備＋その記述** が、所定の位置・視認性で入っているか（UEMO）
- [ ] 送信対象が **DNC登録簿**（ファクシミリ／SMS／事前録音音声）と照合済みか
- [ ] **サプレッションリスト**が全チャネル横断・即時反映か
- [ ] テンプレートの必須要素を **CIのリンターで機械検証**しているか
- [ ] 承認記録（誰が・いつ・どの版を承認したか）が残るか

### 8.3 食品・商品マスタ
- [ ] FEHD の **食品輸入業者／食品販売業者登録**が完了し、取り扱いカテゴリが実態と一致しているか
- [ ] 高リスク食品（食肉/家禽、牛乳・乳飲料、冷菓、水産物）の**事前許可**を取得しているか
- [ ] **日本産10都県の水産物・海塩・海藻加工品**が受注・出荷・カタログのすべてでブロックされるか
- [ ] 禁止リストの更新プロセス（CFS公表監視→承認→反映→証跡）が定義されているか
- [ ] トレーサビリティ記録（移動記録）の保持と検索性
- [ ] 表示・栄養表示の適合、産地/認証の訴求に対する証跡保管

### 8.4 委託先（データ処理者）
- [ ] DPA に **RMC相当条項**（または同等の移転条項）
- [ ] **保持期間制限**と**契約終了時の返却・削除証明**
- [ ] **サブプロセッサの事前承認**と一覧の維持
- [ ] **インシデント通知SLA**（時間単位で規定）
- [ ] セキュリティ要件（暗号化・アクセス制御・監査権）と、監査またはSOC2/ISO報告書の入手
- [ ] 移転レジスタへの反映

---

## 9. 90日ロードマップ

| 期間 | 実施事項 |
|---|---|
| **Day 0–30**<br>止血 | ① マーケティング同意フローの現状棚卸と違反リスクの特定（Part 6A / UEMO）<br>② 日本産禁止品目ブロックの実装・テスト<br>③ 管理者MFA・特権棚卸<br>④ データインベントリ着手（何を・どこに・誰と） |
| **Day 31–60**<br>体制 | ⑤ PICS/PPS の改訂と多言語化<br>⑥ 全委託先のDPA更新（RMC条項）と移転レジスタ完成<br>⑦ インシデント対応プレイブック作成（香港＋日本＋EU分岐）＋e-Formテンプレ<br>⑧ 保持期間ポリシー策定 |
| **Day 61–90**<br>検証 | ⑨ 机上演習（漏えい＋アカウント乗っ取り＋3PL侵害の3シナリオ）<br>⑩ ペネトレーションテストと是正<br>⑪ 生成AI利用ポリシー（PCPDチェックリスト準拠）<br>⑫ TDO観点のUI/表示レビュー（自動更新・欠品・解約導線）<br>⑬ 香港法弁護士による最終レビュー |

---

## 10. 出典

### DLA Piper "Data Protection Laws of the World" — Hong Kong, SAR（本レポートの骨格）
> 注：下記URLは本環境から直接取得できなかったため、内容は検索経由の同サイト要約に基づく。一次確認を推奨。

- [Data protection laws in Hong Kong, SAR（Law）](https://www.dlapiperdataprotection.com/index.html?t=law&c=HK)
- [Definitions in Hong Kong, SAR](https://www.dlapiperdataprotection.com/index.html?t=definitions&c=HK)
- [National data protection authority in Hong Kong, SAR](https://www.dlapiperdataprotection.com/index.html?t=authority&c=HK)
- [Registration in Hong Kong, SAR](https://www.dlapiperdataprotection.com/index.html?t=registration&c=HK)
- [Data protection officers in Hong Kong, SAR](https://www.dlapiperdataprotection.com/index.html?t=data-protection-officers&c=HK)
- [Collection and processing in Hong Kong, SAR](https://www.dlapiperdataprotection.com/index.html?t=collection-and-processing&c=HK)
- [Transfer of personal data in Hong Kong, SAR](https://www.dlapiperdataprotection.com/index.html?t=transfer&c=HK)
- [Security in Hong Kong, SAR](https://www.dlapiperdataprotection.com/index.html?t=security&c=HK)
- [Breach notification in Hong Kong, SAR](https://www.dlapiperdataprotection.com/?t=breach-notification&c=HK)
- [Enforcement in Hong Kong, SAR](https://www.dlapiperdataprotection.com/?t=enforcement&c=HK)
- [Electronic marketing in Hong Kong, SAR](https://www.dlapiperdataprotection.com/index.html?t=electronic-marketing&c=HK)
- [Online privacy in Hong Kong, SAR](https://www.dlapiperdataprotection.com/index.html?t=online-privacy&c=HK)
- [HONG KONG, SAR — Data Protection Laws of the World（国別PDF）](https://www.dlapiperdataprotection.com/guide.pdf?c=HK)

### PCPD（香港 個人資料私隠專員公署）
- [The Personal Data (Privacy) Ordinance（条例概観）](https://www.pcpd.org.hk/english/data_privacy_law/ordinance_at_a_Glance/ordinance.html)
- [Guidance on Data Breach Handling and Data Breach Notifications（2023年6月・PDF）](https://www.pcpd.org.hk/english/resources_centre/publications/files/guidance_note_dbn_e.pdf)
- [PCPD's Updated Guidance On Data Breach](https://www.pcpd.org.hk/english/news_events/newspaper/newspaper_202307.html)
- [Guidance on Direct Marketing（2023年4月・PDF）](https://www.pcpd.org.hk/english/publications/files/GN_DM_e.pdf)
- [Artificial Intelligence: Model Personal Data Protection Framework（PDF）](https://www.pcpd.org.hk/english/resources_centre/publications/files/ai_protection_framework.pdf)
- [AI Privacy Protection（PCPD AI特設ページ）](https://www.pcpd.org.hk/english/artificial_intelligence/index.html)
- [Privacy Commissioner's Office Publishes "AI: Model Personal Data Protection Framework"（2024/6/11 プレスリリース）](https://www.pcpd.org.hk/english/news_events/media_statements/press_20240611.html)
- [Response to media enquiry on data localisation](https://www.pcpd.org.hk/english/news_events/media_enquiry/enquiry_20200415.html)

### 電子マーケティング（UEMO）
- [OFCA — Unsolicited Electronic Messages Ordinance](https://www.ofca.gov.hk/en/industry_focus/industry_focus/uemo/index.html)
- [OFCA — General Information Regarding the UEMO（FAQ）](https://www.ofca.gov.hk/en/consumer_focus/guide/others/uemo/faq_uemo/general_information_uemo/index.html)
- [Communications Authority — Code of Practice under the UEMO（PDF）](https://www.coms-auth.hk/filemanager/statement/en/upload/238/cop20131129.pdf)
- [Unsolicited Electronic Messages Ordinance (Cap. 593) — WIPO Lex](https://www.wipo.int/wipolex/en/legislation/details/15692)

### 消費者保護（TDO）
- [Hong Kong Customs — Trade Descriptions](https://www.customs.gov.hk/en/service-enforcement-information/consumer-protection/trade-desc/index.html)
- [Hong Kong Customs — Unfair Trade Practices](https://www.customs.gov.hk/en/service-enforcement-information/consumer-protection/trade-desc/unfair/index.html)
- [Trade Descriptions (Unfair Trade Practices) (Amendment) Ordinance — Hong Kong Lawyer](https://www.hk-lawyer.org/content/trade-descriptions-unfair-trade-practices-amendment-ordinance)
- [Clicking in Place — The Impact of the New Trade Descriptions Law（オンライン取引への影響）](https://www.hk-lawyer.org/content/clicking-place-impact-new-trade-descriptions-law)
- [The Trade Descriptions Ordinance — Family CLIC](https://familyclic.hk/en/topics/daily-lives-legal-issues/consumer-rights/the-trade-descriptions-ordinance/)

### 食品
- [Cap. 612 Food Safety Ordinance（eLegislation）](https://www.elegislation.gov.hk/hk/cap612)
- [CFS — Food Safety Ordinance](https://www.cfs.gov.hk/english/foodsafetyordinance/food_safety_ordinance.html)
- [CFS — Food Legislation / Guidelines](https://www.cfs.gov.hk/english/food_leg/food_leg.html)
- [CFS — Guide to import of Food into HK](https://www.cfs.gov.hk/english/import/import_icfsg_02.html)
- [CFS — Import/Export of Food FAQ](https://www.cfs.gov.hk/english/faq/faq_06.html)
- [CFS — Online Shopping and Food Safety](https://www.cfs.gov.hk/english/multimedia/multimedia_pub/multimedia_pub_fsf_111_01.html)
- [CFS — Control Measures on Foods Imported from Japan（Q&A）](https://www.cfs.gov.hk/english/programme/programme_rafs/programme_rafs_fc_01_30_Q&A_4.html)
- [CFS — The latest control measures on food imported from Japan](https://www.cfs.gov.hk/english/programme/programme_rafs/programme_rafs_fc_01_30_Nuclear_Event_and_Food_Safety_03.html)
- [LCQ22: Ensuring safety of aquatic food products imported from Japan（2026/4/29）](https://www.info.gov.hk/gia/general/202604/29/P2026042900355.htm)
- [Baker McKenzie — Licensing and approvals requirements to import/export food (Hong Kong)](https://resourcehub.bakermckenzie.com/en/resources/asia-pacific-food-law-guide/asia-pacific/hong-kong/topics/licensing-and-approvals-requirements-to-importexport-food)

### サイバーセキュリティ（Cap. 653）
- [Protection of Critical Infrastructures (Computer Systems) Ordinance to come into effect on January 1, 2026（政府発表）](https://www.info.gov.hk/gia/general/202506/27/P2025062700238.htm)
- [Communications Authority — PCICSO](https://www.coms-auth.hk/en/policies_regulations/other/pcicso/index.html)
- [Mayer Brown — Hong Kong Passes First Cybersecurity Legislation for Regulating Critical Infrastructures](https://www.mayerbrown.com/en/insights/publications/2025/07/hong-kong-passes-first-cybersecurity-legislation-for-regulating-critical-infrastructures)
- [Mayer Brown — Hong Kong issues Code of Practice under the PCICSO（2026/1）](https://www.mayerbrown.com/en/insights/publications/2026/01/hong-kong-issues-code-of-practice-under-the-protection-of-critical-infrastructures-computer-systems-ordinance)
- [Ashurst — Hong Kong passes new cybersecurity law](https://www.ashurst.com/en/insights/hong-kong-passes-new-cybersecurity-law-what-you-need-to-know/)
- [IAPP — Hong Kong's Critical Infrastructure Ordinance provides opportunities for privacy professionals](https://iapp.org/news/a/hong-kong-s-critical-infrastructure-ordinance-provides-opportunities-for-privacy-professionals)

### PDPO 改正動向・その他解説
- [LCQ2: Prevention of personal data breaches and financial crimes（2025/1/22）](https://www.info.gov.hk/gia/general/202501/22/P2025012200305.htm)
- [HFW — A new era for data protection in Hong Kong: legislative updates for a digital age](https://www.hfw.com/insights/a-new-era-for-data-protection-in-hong-kong-legislative-updates-for-a-digital-age/)
- [BCLP — Amendments to Hong Kong Data Protection Law Regarding the PCPD's Sanctioning Powers](https://www.bclplaw.com/en-US/events-insights-news/part-3-of-6-amendments-to-hong-kong-data-protection-law-regarding-the-pcpds-sanctioning-powers.html)
- [Privacy Matters (DLA Piper) — Hong Kong: Updates to the PDPO put on hold](https://privacymatters.dlapiper.com/2024/11/hong-kong-updates-to-the-personal-data-privacy-ordinance-put-on-hold/)
- [Baker McKenzie — Territorial Scope (Hong Kong)](https://resourcehub.bakermckenzie.com/en/resources/global-data-and-cyber-handbook/asia-pacific/hong-kong/topics/territorial-scope)
- [Sidley — Hong Kong New PCPD Guidance on Handling Data Breaches](https://www.sidley.com/en/insights/newsupdates/2023/07/hong-kong-new-pcpd-guidance-on-handling-data-breaches)
- [Bird & Bird — Gen AI at work: HK Privacy Commissioner publishes further AI guidance](https://www.twobirds.com/en/insights/2025/china/gen-ai-at-work-hong-kong-privacy-commissioner)
- [Deacons — Direct marketing best practice: avoiding criminal liability](https://www.deacons.com/2025/04/03/direct-marketing-best-practice-avoiding-criminal-liability/)

---

## 免責

本レポートは公開情報の整理であり、法的助言ではありません。
§0 に記した通り、骨格として参照した DLA Piper サイトには本環境から直接アクセスできず、内容は検索経由の要約に依拠しています。
金額・期限・条番号（「※要一次確認」を付した箇所を含む）および法改正の最新状況は、
eLegislation・PCPD・CFS・香港税関の一次情報で確認し、実施前に香港法資格を有する弁護士のレビューを受けてください。
