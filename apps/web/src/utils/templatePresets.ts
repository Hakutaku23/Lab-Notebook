import type { TemplateSectionPayload } from "../types/api";

function genericSections(): TemplateSectionPayload[] {
  return [
    {
      key: "basic_info",
      title: "基础信息",
      description: "记录实验名称、日期与目的。",
      order_index: 0,
      is_repeatable: false,
      fields: [
        {
          key: "experiment_name",
          label: "实验名称",
          field_type: "text",
          required: true,
          order_index: 0,
          placeholder: "例如：酸碱中和反应实验",
        },
        {
          key: "experiment_date",
          label: "实验日期",
          field_type: "date",
          required: true,
          order_index: 1,
        },
        {
          key: "objective",
          label: "实验目的",
          field_type: "textarea",
          required: true,
          order_index: 2,
          placeholder: "记录本次实验要验证的问题与目标。",
        },
      ],
    },
    {
      key: "procedure",
      title: "实验过程",
      description: "记录关键步骤、现象与条件。",
      order_index: 1,
      is_repeatable: false,
      fields: [
        {
          key: "procedure_notes",
          label: "过程记录",
          field_type: "textarea",
          required: true,
          order_index: 0,
          placeholder: "按时间顺序记录操作步骤。",
        },
        {
          key: "result_summary",
          label: "结果与结论",
          field_type: "textarea",
          required: false,
          order_index: 1,
          placeholder: "记录实验结果、误差分析与结论。",
        },
      ],
    },
  ];
}

function chemistrySections(): TemplateSectionPayload[] {
  return [
    {
      key: "basic_info",
      title: "实验基础信息",
      description: "适用于常见化学实验的基础记录。",
      order_index: 0,
      is_repeatable: false,
      fields: [
        {
          key: "experiment_name",
          label: "实验名称",
          field_type: "text",
          required: true,
          order_index: 0,
          placeholder: "例如：乙酸乙酯的制备",
        },
        {
          key: "experiment_date",
          label: "实验日期",
          field_type: "date",
          required: true,
          order_index: 1,
        },
        {
          key: "experiment_type",
          label: "实验类型",
          field_type: "select",
          required: false,
          order_index: 2,
          options: {
            items: [
              { label: "无机化学", value: "inorganic" },
              { label: "有机化学", value: "organic" },
              { label: "分析化学", value: "analytical" },
              { label: "物理化学", value: "physical" },
            ],
          },
        },
        {
          key: "objective",
          label: "实验目的",
          field_type: "textarea",
          required: true,
          order_index: 3,
          placeholder: "记录实验目标、原理与预期结果。",
        },
      ],
    },
    {
      key: "materials",
      title: "试剂与器材",
      description: "试剂可用表格/JSON，器材可用文本。",
      order_index: 1,
      is_repeatable: false,
      fields: [
        {
          key: "reagents",
          label: "试剂清单",
          field_type: "table",
          required: false,
          order_index: 0,
          placeholder: '例如：[{"name":"乙酸","amount":"10 mL"}]',
          help_text: "支持 JSON、CSV 或 Markdown 表格。",
        },
        {
          key: "apparatus",
          label: "仪器与装置",
          field_type: "textarea",
          required: false,
          order_index: 1,
          placeholder: "记录主要仪器、装置和玻璃器皿。",
        },
      ],
    },
    {
      key: "reaction",
      title: "反应与过程",
      description: "化学方向特异化字段。",
      order_index: 2,
      is_repeatable: false,
      fields: [
        {
          key: "chemical_equation",
          label: "化学反应方程式",
          field_type: "chemical_equation",
          required: true,
          order_index: 0,
          help_text: "可直接录入反应物和生成物，也可切换到手写模式。",
          ui_props: { arrow: "→", mode: "structured" },
        },
        {
          key: "reaction_process",
          label: "反应过程记录",
          field_type: "reaction_process",
          required: false,
          order_index: 1,
          help_text: "建议按步骤记录操作、条件、现象和预期结果。",
        },
      ],
    },
    {
      key: "result_analysis",
      title: "结果分析",
      description: "记录产物情况、现象与误差分析。",
      order_index: 3,
      is_repeatable: false,
      fields: [
        {
          key: "observation",
          label: "实验现象",
          field_type: "textarea",
          required: false,
          order_index: 0,
          placeholder: "颜色变化、沉淀、气泡、温度变化等。",
        },
        {
          key: "yield_or_result",
          label: "产率/结果数据",
          field_type: "json",
          required: false,
          order_index: 1,
          placeholder: '{"yield":"72%","purity":"95%"}',
        },
        {
          key: "analysis",
          label: "分析与结论",
          field_type: "textarea",
          required: false,
          order_index: 2,
          placeholder: "记录原因分析、误差来源和结论。",
        },
      ],
    },
  ];
}

export function buildTemplatePreset(kind: "generic" | "chemistry") {
  if (kind === "chemistry") {
    return {
      name: "化学实验基础模板",
      key: "chemistry-experiment-basic-v1",
      category: "chemistry",
      description: "包含化学反应方程式与反应过程步骤记录的基础模板。",
      sections: chemistrySections(),
    };
  }

  return {
    name: "通用实验模板",
    key: "generic-experiment-v1",
    category: "generic",
    description: "适用于多数实验场景的基础模板。",
    sections: genericSections(),
  };
}
