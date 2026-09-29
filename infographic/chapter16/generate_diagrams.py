"""Same semantic scenes produce SVG and bound Tldraw source, without AI text."""
import json
from pathlib import Path
from infographic.chapter14.generate_diagrams import Scene, Node, Edge, _svg, _tldraw

def n(key,label,x,y,color,w=300,h=130):
    return Node(key,label,x,y,w,h,color)

def chain(*ids,color="blue"):
    return tuple(Edge("e"+str(i),a,b,color=color) for i,(a,b) in enumerate(zip(ids,ids[1:]),1))

def build_scenes():
    return (
      Scene("01-two-improvement-loops","两个循环：纠错不等于持续改进","上方修好当前任务；下方决定未来运行用什么。",
       (n("input","当前请求",80,240,"blue",250),n("action","行动与反馈",420,240,"violet",280),
        n("repair","当前修正",810,240,"green",250),n("end","当前任务结束",1220,240,"orange",280),
        n("evidence","合格失败证据",80,570,"blue",250),n("asset","范围化候选",420,570,"violet",280),
        n("verify","独立验收 + 审批",810,570,"green",300),n("next","后续运行实际消费",1220,570,"orange",300)),
       chain("input","action","repair","end")+tuple(Edge("long"+str(i),a,b,color="green") for i,(a,b) in enumerate(zip(("evidence","asset","verify"),("asset","verify","next")),1))+
       (Edge("bridge","action","evidence","采集，不直接激活","violet","dashed",70),),
       "短循环改变这次产物；长循环改变有证据、有范围、可停用的未来行为。"),
      Scene("02-feedback-evidence-funnel","反馈证据漏斗","输入十二条反馈，先核验再提案；状态不是四个分数。",
       (n("raw","原始反馈\n12 条",110,200,"blue",300),n("redact","类型 + 来源敏感检查\n脱敏仍保留标记",630,200,"violet",600),
        n("authority","来源 / 用途 / 权限\n范围 + 完整性 + 去重",450,420,"blue",700,110),
        n("accepted","accepted 6\n证据，不等于资产",60,650,"green",320,110),n("quarantine","quarantined 3\n攻击 / 敏感 / 泄漏",460,650,"red",320,110),
        n("merged","merged 1\n保留血缘，不增独立数",860,650,"violet",320,110),n("unknown","Unknown 2\n缺回执 / 冲突",1230,650,"orange",300,110)),
       chain("raw","redact","authority")+tuple(Edge("branch"+str(i),"authority",target,color=color) for i,(target,color) in enumerate((("accepted","green"),("quarantine","red"),("merged","violet"),("unknown","orange")),1)),
       "反馈只能申请改变；权限来自可信注册表，Unknown 不能被改写为成功。"),
      Scene("03-replay-and-attribution","固定回放：一次只换一个条件","冻结输入、文档、权限、工具回执、Agent版本和时钟。",
       (n("frozen","相同冻结条件\n相同 frozen_hash",560,230,"blue",460),n("base","基线\n旧文档 / 漏步骤",560,430,"grey",460),
        n("selection","只换选择策略\nF01 文档改变",60,650,"green",350,110),
        n("procedure","只换步骤策略\nF03 步骤改变",560,650,"violet",460,110),
        n("missing","不完整条件\n环境错误 / Unknown",1130,430,"orange",380),
        n("limits","保留缺失\n不补造回执",1130,650,"red",380,110)),
       (Edge("e1","frozen","base"),Edge("e2","base","selection","selection"),Edge("e3","base","procedure","procedure","violet"),
        Edge("e4","frozen","missing","缺失/超时","orange"),Edge("e5","missing","limits","不能归功于修复","red")),
       "两份可回放 / 四份案例；因果假设只成立于这些固定教学条件。"),
      Scene("04-improvement-carriers","不同缺陷，放入不同载体","三类资产真实消费；其他载体仍是提案，不伪装成已实现。",
       tuple(n(key,label,x,y,color,w=350,h=110) for key,label,x,y,color in (
         ("knowledge","选错当前文档",70,240,"blue"),("krule","knowledge_rule",600,240,"blue"),("selector","授权文档选择器",1130,240,"green"),
         ("procedure","遗漏必要步骤",70,420,"violet"),("skill","step_skill",600,420,"violet"),("executor","允许表内步骤解释器",1130,420,"green"),
         ("preference","用户 A 偏好",70,600,"orange"),("memory","scoped_memory",600,600,"orange"),("style","仅调整格式",1130,600,"green")))+
         (n("proposal","Prompt / Harness / 训练数据：仅提案或导出，不进入可执行快照",180,750,"grey",1240,60),),
       (Edge("k1","knowledge","krule"),Edge("k2","krule","selector"),Edge("s1","procedure","skill",color="violet"),Edge("s2","skill","executor",color="violet"),
        Edge("m1","preference","memory",color="orange"),Edge("m2","memory","style",color="orange")),
       "看 document_id、steps、answer_style 与 applied_artifacts，不看“我学会了”。"),
      Scene("05-artifact-promotion","候选晋级：材料绑定，三态门禁","通过验收仍须审批；改变条件不能复用旧批准。",
       (n("candidate","有范围候选\n未批准",60,290,"violet",260),n("eval","独立验收\n安全 → 证据 → 回归",440,290,"blue",320),
        n("approval","可信批准入口\n绑定候选 / 证据 / 上下文",850,290,"orange",330),n("active","激活指针\n批准且未到期",1260,290,"green",270),
        n("failure","fail / inconclusive\n拒绝 / 补证据",420,640,"red",360),n("changed","内容或条件变化\n重新验证",950,640,"violet",470)),
       (Edge("e1","candidate","eval"),Edge("e2","eval","approval","pass","green"),Edge("e3","approval","active","授权","green"),
        Edge("e4","eval","failure","缺失/违规","red"),Edge("e5","active","changed","变更","orange"),Edge("e6","changed","eval","新证据","violet","dashed",70)),
       "批准的是完整材料身份与范围，不是一个可重复使用的“同意”。"),
      Scene("06-feedback-poisoning","改进通道也是攻击通道","来源血缘与独立真值，阻止危险文本变成持久经验。",
       (n("payload","关闭审批 / 复制隐藏答案\n伪装成经验建议",50,280,"red",360),n("admission","来源 / 用途准入\n敏感血缘保留",530,280,"violet",380),
        n("asset","有来源的候选\n不能读隐藏真值",1120,280,"blue",380),n("blocked","隔离与 Unknown\n不提升为资产",460,600,"orange",400),
        n("truth","独立真值 + 反例\n发现过度泛化",1090,600,"green",430),n("self","自生成总结不算新来源\n沿血缘追到根证据",40,600,"grey",320)),
       (Edge("e1","payload","admission","只作输入","red"),Edge("e2","admission","asset","仅合格证据","green"),Edge("e3","admission","blocked","不合格","orange"),
        Edge("e4","asset","truth","验收","green"),Edge("e5","self","blocked","防自我洗白","violet","dashed")),
       "文本不能自行提升权限；转述多次仍是同一根证据。"),
      Scene("07-canary-and-rollback","离线灰度：停止后保留证据","稳定分桶4/12，不估计真实A/B收益；到期探针是显式新条件。",
       (n("cohort","seed 1601\n稳定请求分桶",60,380,"blue",280),n("base","基线 12\n继续旧版本",440,230,"grey",300),
        n("candidate","候选 4\n有批准版本",440,570,"green",300),n("probe","推进时钟\n过期探针失败",880,570,"orange",290),
        n("stop","stop → rollback\n已知历史指针",1250,570,"red",300),n("policy","当前 UsePolicy + 时钟\n回滚不能恢复撤销许可",850,230,"violet",670),
        n("effects","外部副作用不能撤回\n历史审计不删除",850,710,"grey",670,100)),
       (Edge("e1","cohort","base","12","grey"),Edge("e2","cohort","candidate","4","green"),Edge("e3","candidate","probe","检测","orange"),Edge("e4","probe","stop","停止","red"),
        Edge("e5","policy","stop","继续过滤","violet","dashed")),
       "回滚不洗白失效资产、不擦除发布历史，也不代替外部副作用补偿。"),
    )

def generate(root: Path):
    source_dir = root/"infographic/chapter16"
    image_dir = root/"book/images/chapter16"
    source_dir.mkdir(parents=True,exist_ok=True)
    image_dir.mkdir(parents=True,exist_ok=True)
    outputs = []
    for scene in build_scenes():
        source, svg = source_dir/(scene.stem+".tldr"), image_dir/(scene.stem+".svg")
        source.write_text(json.dumps(_tldraw(scene),ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
        svg.write_text(_svg(scene),encoding="utf-8",newline="\n")
        outputs.extend((source,svg))
    return tuple(outputs)

if __name__ == "__main__":
    root = Path(__file__).parents[2]
    for path in generate(root):
        print(path.relative_to(root))
