import fs from 'fs';

const notes = JSON.parse(fs.readFileSync('all_notes_with_time.json', 'utf8'));
const comments = JSON.parse(fs.readFileSync('comments_dir1.json', 'utf8'));

const num = s => {
  if (typeof s === 'number') return s;
  if (!s) return 0;
  s = String(s).trim();
  if (s.includes('万')) return Math.round(parseFloat(s) * 10000);
  return parseInt(s.replace(/[^\d]/g, ''), 10) || 0;
};

// ===== A. 虚拟品选品参考（笔记层）=====
const vpKw = ['小红书 虚拟品', '虚拟资料 赚钱'];
const vpNotes = notes.filter(n => vpKw.includes(n.kw))
  .map(n => ({ kw: n.kw, title: n.title, liked: num(n.liked), pub: n.pubTime }))
  .sort((a, b) => b.liked - a.liked);
console.log(`\n===== A. 虚拟品方向高赞笔记（共 ${vpNotes.length} 条，取 Top 25）=====`);
vpNotes.slice(0, 25).forEach((n, i) =>
  console.log(`${String(i + 1).padStart(2)}. [${n.liked}赞|${n.kw}|${n.pub}] ${n.title}`));

// ===== B. 虚拟品评论诉求（评论层）=====
const vpComments = comments.filter(c => c.noteKw === '小红书 虚拟品')
  .map(c => ({ ...c, _liked: num(c.liked) }));
console.log(`\n===== B. 小红书虚拟品评论诉求（共 ${vpComments.length} 条）=====`);
const vpCats = {
  '求教程/怎么做': /怎么(做|弄|搞|卖|起号|引流)|教程|教学|步骤|流程|0-?1|从零|实操|保姆/,
  '求资料/模板/资源': /资料|模板|素材|资源|文档|清单|表|合集|打包|发我|私|求(分|带)/,
  '求带/变现/接单': /带我|收徒|变现|赚钱|赚到|副业|接单|引流|获客|客源|怎么(挣|赚)/,
  '问选品/卖什么': /卖什么|选品|什么(好卖|能卖)|品类|爆款|蓝海|需求/,
  '吐槽/焦虑': /割韭菜|智商税|坑|骗|难|卷|雷|违规|限流|封/,
};
const vpCount = {}; const vpSamples = {};
for (const k of Object.keys(vpCats)) { vpCount[k] = 0; vpSamples[k] = []; }
for (const c of vpComments) {
  for (const k of Object.keys(vpCats)) {
    if (vpCats[k].test(c.content)) {
      vpCount[k]++;
      if (vpSamples[k].length < 5 && c._liked >= 1 && c.content.length > 5)
        vpSamples[k].push({ t: c.content, l: c._liked });
    }
  }
}
for (const k of Object.keys(vpCats))
  console.log(`${k.padEnd(16)} : ${vpCount[k]} 条`);
console.log('--- 虚拟品高赞评论样本（赞>=3）---');
vpComments.filter(c => c._liked >= 3).sort((a, b) => b._liked - a._liked)
  .slice(0, 25).forEach(c => console.log(`[${c._liked}赞] ${c.content}`));

// ===== C. 引流标题模板（信息整理 / AI知识管理 高赞）=====
const flowKw = ['信息整理 AI', 'AI 知识管理'];
const flowNotes = notes.filter(n => flowKw.includes(n.kw))
  .map(n => ({ kw: n.kw, title: n.title, liked: num(n.liked) }))
  .sort((a, b) => b.liked - a.liked);
console.log(`\n===== C. 引流高赞标题（${flowKw.join('/')}，共 ${flowNotes.length} 条，取 Top 30）=====`);
flowNotes.slice(0, 30).forEach((n, i) =>
  console.log(`${String(i + 1).padStart(2)}. [${n.liked}赞|${n.kw}] ${n.title}`));

// 标题公式词频
const formulaWords = ['教程', '拆解', '保姆', '0基础', '0-1', '案例', '模板', '怎么', '实操', '干货', '普通人', '打工人', '小白', '进阶', '实战', '盘点', '合集', '避雷', '神器', '自动化', '搭建', '从零', '一套', '吃透', '背下来', '建立'];
const wf = {};
for (const n of flowNotes) for (const w of formulaWords) if (n.title.includes(w)) wf[w] = (wf[w] || 0) + 1;
console.log('\n--- 引流标题高频公式词 ---');
Object.entries(wf).sort((a, b) => b[1] - a[1]).forEach(([w, c]) => console.log(`${w}: ${c}`));

// 导出
fs.writeFileSync('actionables.json', JSON.stringify({
  vpNotes: vpNotes.slice(0, 25),
  vpCommentCount: vpCount,
  vpCommentSamples: vpSamples,
  vpHighComments: vpComments.filter(c => c._liked >= 3).sort((a, b) => b._liked - a._liked).slice(0, 25).map(c => ({ liked: c._liked, content: c.content })),
  flowNotes: flowNotes.slice(0, 30),
  flowWordFreq: wf,
}, null, 2));
console.log('\n已导出 actionables.json');
