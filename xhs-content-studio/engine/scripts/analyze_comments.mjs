import fs from 'fs';

const d = JSON.parse(fs.readFileSync('comments_dir1.json', 'utf8'));
console.log('总评论数:', d.length);

// 1. liked 转数值
const num = s => {
  if (typeof s === 'number') return s;
  if (!s) return 0;
  s = String(s).trim();
  if (s.includes('万')) return Math.round(parseFloat(s) * 10000);
  return parseInt(s.replace(/[^\d]/g, ''), 10) || 0;
};
for (const c of d) c._liked = num(c.liked);

// 2. 诉求聚类
const cats = {
  '求教程/怎么学': /怎么(学|做|用|搞|玩|搭)|教我|求教|教程|教学|学习|入门|小白|从零|手把手|不会用|怎么搞|求攻略|求步骤/,
  '求工具/软件/资源': /什么工具|哪个(软件|app|工具)|软件|工具|资源|网站|平台|链接|源码|哪里(找|下|弄)|有(没有|无)这个(软件|工具)|神器|插件/,
  '求带/接单/变现': /带我|收徒|怎么接单|接单|副业|赚钱|变现|兼职|合作|引流|怎么(挣|赚)|客单|报价|渠道|获客/,
  '求模板/资料/文件': /模板|资料|文档|笔记|导图|清单|表格|文件|课件|合集|整理(好|过)|发我|私(我|聊)|求(分享|发)/,
  '对比/选型/推荐': /区别|对比|哪个好|选哪个|推荐(一|个|下)|好不好|值不值|有必要|要不要/,
  '焦虑/困惑/劝退': /会不会|担心|焦虑|迷茫|不懂|看不懂|太难|劝退|踩坑|坑|割韭菜|智商税|怕/,
};
const catCount = {}; const catSamples = {};
for (const k of Object.keys(cats)) { catCount[k] = 0; catSamples[k] = []; }
for (const c of d) {
  for (const k of Object.keys(cats)) {
    if (cats[k].test(c.content)) {
      catCount[k]++;
      if (catSamples[k].length < 6 && c._liked >= 3 && c.content.length > 6)
        catSamples[k].push({ t: c.content, l: c._liked, kw: c.noteKw });
    }
  }
}

console.log('\n===== 诉求类型分布（评论层真人信号）=====');
for (const k of Object.keys(cats))
  console.log(`${k.padEnd(18)} : ${catCount[k]} 条`);

// 3. 按关键词分组：评论数 + 平均赞 + 高赞诉求
const byKw = {};
for (const c of d) {
  const k = c.noteKw;
  if (!byKw[k]) byKw[k] = { n: 0, likeSum: 0, highAsk: [] };
  byKw[k].n++; byKw[k].likeSum += c._liked;
  if (/求教|怎么(学|做|用)|教程|工具|软件|模板|资料|接单|变现|带我/.test(c.content) && c.content.length > 6)
    byKw[k].highAsk.push({ t: c.content, l: c._liked });
}
console.log('\n===== 各关键词评论活跃度 =====');
const kwRows = Object.entries(byKw).map(([k, v]) => ({ k, n: v.n, avg: Math.round(v.likeSum / v.n), ask: v.highAsk.length }));
kwRows.sort((a, b) => b.n - a.n);
for (const r of kwRows)
  console.log(`${r.k.padEnd(14)} 评论 ${String(r.n).padStart(3)} | 均赞 ${String(r.avg).padStart(4)} | 诉求信号 ${r.ask}`);

// 4. 高赞长评金矿（真人原话）
const gold = d.filter(c => c._liked >= 10 && c.content.length > 8)
  .sort((a, b) => b._liked - a._liked);
console.log(`\n===== 高赞真人原话（赞>=10 且 长度>8，共 ${gold.length} 条，取前 50）=====`);
for (const c of gold.slice(0, 50))
  console.log(`[${c._liked}赞|${c.noteKw}] ${c.content}`);

// 5. 导出结构化
const out = {
  total: d.length,
  catCount,
  kwRows,
  gold: gold.slice(0, 80).map(c => ({ liked: c._liked, kw: c.noteKw, title: c.noteTitle, content: c.content })),
};
fs.writeFileSync('comments_analyzed.json', JSON.stringify(out, null, 2,));
console.log('\n已导出 comments_analyzed.json');
