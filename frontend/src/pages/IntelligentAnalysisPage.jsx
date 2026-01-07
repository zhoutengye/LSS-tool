import { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Steps,
  Alert,
  Spin,
  message,
  Row,
  Col,
  Typography,
  Divider,
  Tag,
  Space,
  Timeline,
  Statistic
} from 'antd';
import {
  ExperimentOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  BulbOutlined,
  RocketOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';

const { Step } = Steps;
const { Title, Paragraph, Text } = Typography;

/**
 * 智能综合分析页面
 *
 * 模拟精益六西格玛黑带专家的思维模式：
 * 1. 自动串联多个工具
 * 2. 综合分析给出结论
 * 3. 提供可执行的改进方案
 */
const IntelligentAnalysisPage = () => {
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [analysisResult, setAnalysisResult] = useState(null);

  // 运行完整的黑带分析流程
  const runBlackBeltAnalysis = async () => {
    setLoading(true);
    setCurrentStep(0);
    setAnalysisResult(null);

    try {
      message.info('🎯 启动精益六西格玛黑带分析流程...');

      // ========== 步骤1: 问题定义 ==========
      setCurrentStep(1);
      await new Promise(resolve => setTimeout(resolve, 800));
      message.info('📋 步骤1: 识别关键问题...');

      // 运行帕累托图识别关键问题
      const paretoRes = await axios.get('http://127.0.0.1:8000/api/lss/pareto/demo');
      const paretoAnalysis = await axios.post(
        'http://127.0.0.1:8000/api/lss/pareto/analyze',
        {
          categories: paretoRes.data.data,
          threshold: 0.8
        }
      );

      // Extract key problems with full details from sorted_data
      const sortedData = paretoAnalysis.data?.result?.sorted_data || [];
      const keyFewNames = paretoAnalysis.data?.result?.key_few || [];
      const keyProblems = sortedData.filter(item => keyFewNames.includes(item.category));
      message.success(`✅ 识别出 ${keyProblems.length} 个关键问题`);

      // ========== 步骤2: 过程能力评估 ==========
      setCurrentStep(2);
      await new Promise(resolve => setTimeout(resolve, 800));
      message.info('📊 步骤2: 评估过程能力...');

      const spcRes = await axios.post('http://127.0.0.1:8000/api/lss/spc/analyze', {
        param_code: 'P_E01_TEMP',
        node_code: 'E01',
        limit: 50
      });

      const cpk = spcRes.data?.result?.result?.cpk ?? 1.0;
      const processStatus = spcRes.data?.result?.result?.process_status ?? '未知';
      message.success(`✅ Cpk = ${cpk.toFixed(3)}, 过程${processStatus}`);

      // ========== 步骤3: 分布形态分析 ==========
      setCurrentStep(3);
      await new Promise(resolve => setTimeout(resolve, 800));
      message.info('📈 步骤3: 分析数据分布...');

      const histogramRes = await axios.post('http://127.0.0.1:8000/api/lss/histogram/analyze', {
        param_code: 'P_E01_TEMP',
        node_code: 'E01',
        limit: 100,
        bins: 10
      });

      const isNormal = histogramRes.data?.result?.statistics?.is_normal ?? true;
      const skewness = histogramRes.data?.result?.statistics?.skewness ?? 0;
      message.success(`✅ 分布${isNormal ? '符合' : '不符合'}正态，偏度=${skewness.toFixed(3)}`);

      // ========== 步骤4: 对比分析 ==========
      setCurrentStep(4);
      await new Promise(resolve => setTimeout(resolve, 800));
      message.info('🔍 步骤4: 车间对比分析...');

      const boxplotRes = await axios.get('http://127.0.0.1:8000/api/lss/boxplot/demo');
      const boxplotAnalysis = await axios.post(
        'http://127.0.0.1:8000/api/lss/boxplot/analyze',
        {
          param_codes: boxplotRes.data.config.param_codes,
          limit_per_series: 50
        }
      );

      const comparison = boxplotAnalysis.data?.result?.comparison ?? { most_variable: 'E01车间', most_variable_series: 'P_E01_TEMP' };
      message.success(`✅ ${comparison.most_variable || 'E01车间'} 波动最大`);

      // ========== 步骤5: 综合诊断 ==========
      setCurrentStep(5);
      await new Promise(resolve => setTimeout(resolve, 1000));

      // 模拟黑带专家的综合分析逻辑
      const diagnosis = generateBlackBeltDiagnosis({
        keyProblems,
        cpk,
        processStatus,
        isNormal,
        skewness,
        comparison,
        spcViolations: spcRes.data?.result?.plot_data?.violations?.length || 0,
        outliers: boxplotAnalysis.data?.result?.total_outliers || 0
      });

      console.log('🔍 Diagnosis generated:', diagnosis);
      console.log('🔍 Improvements:', diagnosis.improvements);
      console.log('🔍 Key problems:', diagnosis.keyProblems);
      console.log('🔍 Full diagnosis JSON:', JSON.stringify(diagnosis, null, 2));

      setAnalysisResult(diagnosis);
      setCurrentStep(5);
      message.success('🎉 综合分析完成！');

    } catch (error) {
      console.error('分析失败:', error);
      message.error('分析失败: ' + error.message);
      setCurrentStep(0);
    } finally {
      setLoading(false);
    }
  };

  // 黑带专家综合诊断逻辑
  const generateBlackBeltDiagnosis = (data) => {
    const {
      keyProblems,
      cpk,
      processStatus,
      isNormal,
      skewness,
      comparison,
      spcViolations,
      outliers
    } = data;

    // 1. 能力等级判定
    let capabilityLevel = '';
    let capabilityColor = '';
    if (cpk >= 1.33) {
      capabilityLevel = '优秀 (A级)';
      capabilityColor = '#52c41a';
    } else if (cpk >= 1.0) {
      capabilityLevel = '良好 (B级)';
      capabilityColor = '#faad14';
    } else if (cpk >= 0.67) {
      capabilityLevel = '勉强 (C级)';
      capabilityColor = '#ff7a45';
    } else {
      capabilityLevel = '不足 (D级)';
      capabilityColor = '#ff4d4f';
    }

    // 2. 根因分析
    const rootCauses = [];
    if (!isNormal) {
      if (Math.abs(skewness) > 1) {
        rootCauses.push({
          cause: '数据分布偏态',
          evidence: `偏度=${skewness.toFixed(2)}，说明过程存在系统性偏差`,
          impact: 'high'
        });
      }
      rootCauses.push({
        cause: '非正态分布',
        evidence: 'Shapiro-Wilk检验p<0.05，不符合正态假设',
        impact: 'medium'
      });
    }

    if (spcViolations > 0) {
      rootCauses.push({
        cause: '过程不稳定',
        evidence: `检测到${spcViolations}个控制图违规点`,
        impact: 'high'
      });
    }

    if (cpk < 1.0) {
      rootCauses.push({
        cause: '过程能力不足',
        evidence: `Cpk=${cpk.toFixed(2)} < 1.0，低于六西格玛标准`,
        impact: 'high'
      });
    }

    if (outliers > 0) {
      rootCauses.push({
        cause: '异常值过多',
        evidence: `箱线图检测到${outliers}个异常值`,
        impact: 'medium'
      });
    }

    // 3. 综合结论
    let conclusion = '';
    let priority = '';

    const highImpactCount = rootCauses.filter(r => r.impact === 'high').length;

    if (cpk >= 1.33 && spcViolations === 0 && isNormal) {
      conclusion = '过程受控且能力充足，建议保持当前控制策略，定期监控。';
      priority = 'low';
    } else if (cpk >= 1.0 && highImpactCount <= 1) {
      conclusion = '过程基本受控，存在局部改进空间，建议针对性优化。';
      priority = 'medium';
    } else if (cpk >= 0.67 || highImpactCount <= 2) {
      conclusion = '过程能力不足或存在明显异常，需要立即启动改进项目。';
      priority = 'high';
    } else {
      conclusion = '过程严重失控，需要停线检查并全面整改。';
      priority = 'critical';
    }

    // 4. 改进建议（DMAIC路径）
    const improvements = [];

    // Define阶段 - 添加安全检查
    const topProblems = keyProblems.slice(0, 2).filter(p => p && p.category);
    const problemNames = topProblems.length > 0 ? topProblems.map(p => p.category).join('、') : '温度异常、压力异常';

    improvements.push({
      phase: 'Define',
      actions: [
        `聚焦关键问题: ${problemNames}`,
        `设定改进目标: Cpk从${cpk.toFixed(2)}提升至${Math.min(cpk + 0.5, 1.67).toFixed(2)}`
      ]
    });

    // Measure阶段
    improvements.push({
      phase: 'Measure',
      actions: [
        '建立测量系统分析(MSA)，确保数据可靠性',
        isNormal ? '继续使用控制图监控' : '先进行数据变换，再使用控制图',
        '收集不少于100个数据点以验证改进效果'
      ]
    });

    // Analyze阶段 - 添加安全检查
    const validRootCauses = rootCauses.filter(rc => rc && rc.cause);
    if (validRootCauses.length > 0) {
      improvements.push({
        phase: 'Analyze',
        actions: validRootCauses.map(rc => `验证根因: ${rc.cause} - ${rc.evidence || '待验证'}`)
      });
    } else {
      improvements.push({
        phase: 'Analyze',
        actions: [
          '使用鱼骨图分析潜在根本原因',
          '通过5Why分析法深挖问题源头',
          '验证人、机、料、法、环各要素的影响'
        ]
      });
    }

    // Improve阶段
    improvements.push({
      phase: 'Improve',
      actions: [
        cpk < 1.0 ? '优化工艺参数，减少变异（DOE实验设计）' : '标准化最佳实践，编写SOP',
        spcViolations > 0 ? '实施统计过程控制(SPC)，设置预警机制' : '保持现有控制策略，定期审查',
        '开展试点验证，收集改善前后对比数据'
      ]
    });

    // Control阶段
    improvements.push({
      phase: 'Control',
      actions: [
        '建立控制计划(Control Plan)，明确监控频率',
        '培训操作人员，确保新方法得到有效执行',
        '制定持续改进流程，设立年度审查机制',
        '更新FMEA和Control Plan文件'
      ]
    });

    // 5. 预期收益
    const expectedBenefits = [];
    if (cpk < 1.33) {
      const defectReduction = ((1.33 - cpk) * 100).toFixed(0);
      expectedBenefits.push(`缺陷率预计降低 ${defectReduction}%`);
    }
    if (spcViolations > 0) {
      expectedBenefits.push(`过程稳定性提升 ${Math.min(spcViolations * 10, 50)}%`);
    }
    if (comparison.most_variable) {
      expectedBenefits.push(`向标杆车间${comparison.max_median_series || '最佳实践'}学习，减少变异`);
    }
    expectedBenefits.push('建立数据驱动的持续改进文化');

    return {
      capabilityLevel,
      capabilityColor,
      cpk,
      processStatus,
      rootCauses,
      conclusion,
      priority,
      improvements,
      expectedBenefits,
      keyProblems: keyProblems.slice(0, 3),
      analysisTime: new Date().toLocaleString()
    };
  };

  // 准备雷达图数据
  const getRadarOption = () => {
    if (!analysisResult) return {};

    return {
      title: {
        text: '过程健康度评估',
        left: 'center'
      },
      radar: {
        indicator: [
          { name: '过程能力', max: 2 },
          { name: '稳定性', max: 100 },
          { name: '正态性', max: 100 },
          { name: '控制水平', max: 100 },
          { name: '改进空间', max: 100 }
        ]
      },
      series: [{
        type: 'radar',
        data: [{
          value: [
            analysisResult.cpk,
            Math.max(0, 100 - (analysisResult.rootCauses.filter(r => r.impact === 'high').length * 20)),
            analysisResult.rootCauses.find(r => r.cause === '非正态分布') ? 60 : 90,
            analysisResult.cpk >= 1.0 ? 80 : 50,
            analysisResult.priority === 'low' ? 40 : 80
          ],
          name: '当前状态',
          areaStyle: {
            color: analysisResult.capabilityColor
          }
        }]
      }]
    };
  };

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      {/* 页面标题 */}
      <Card style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              <ExperimentOutlined /> 精益六西格玛智能分析系统
            </Title>
            <Paragraph type="secondary" style={{ marginTop: 8 }}>
              模拟黑带专家思维 · 工具联合分析 · 综合诊断结论
            </Paragraph>
          </div>

          <Button
            type="primary"
            size="large"
            icon={<RocketOutlined />}
            onClick={runBlackBeltAnalysis}
            loading={loading}
          >
            启动黑带分析流程
          </Button>
        </Space>
      </Card>

      {/* 分析进度 */}
      {loading && (
        <Card style={{ marginBottom: 24 }}>
          <Steps current={currentStep}>
            <Step title="准备" description="初始化分析环境" />
            <Step title="问题定义" description="帕累托图识别关键问题" />
            <Step title="能力评估" description="SPC控制图分析Cpk" />
            <Step title="分布分析" description="直方图检验正态性" />
            <Step title="对比分析" description="箱线图对比车间差异" />
            <Step title="综合诊断" description="生成改进方案" />
          </Steps>
          <Divider />
          <Spin tip="正在运行黑带分析流程，请稍候..." />
        </Card>
      )}

      {/* 分析结果 */}
      {analysisResult && (
        <div>
          {/* 核心结论 */}
          <Card
            title={
              <span>
                <FileTextOutlined /> 黑带专家综合诊断报告
              </span>
            }
            style={{ marginBottom: 24 }}
            extra={
              <Tag color={
                analysisResult.priority === 'critical' ? 'red' :
                analysisResult.priority === 'high' ? 'orange' :
                analysisResult.priority === 'medium' ? 'blue' : 'green'
              }>
                优先级: {
                  analysisResult.priority === 'critical' ? '紧急' :
                  analysisResult.priority === 'high' ? '高' :
                  analysisResult.priority === 'medium' ? '中' : '低'
                }
              </Tag>
            }
          >
            {/* 能力等级 */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={8}>
                <Card>
                  <Statistic
                    title="过程能力等级"
                    value={analysisResult.capabilityLevel}
                    valueStyle={{ color: analysisResult.capabilityColor, fontSize: '24px' }}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card>
                  <Statistic
                    title="Cpk指数"
                    value={analysisResult.cpk}
                    precision={3}
                    valueStyle={{ color: analysisResult.capabilityColor }}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card>
                  <Statistic
                    title="过程状态"
                    value={analysisResult.processStatus}
                    valueStyle={{
                      color: analysisResult.processStatus === '受控' ? '#52c41a' : '#ff4d4f',
                      fontSize: '20px'
                    }}
                  />
                </Card>
              </Col>
            </Row>

            {/* 雷达图 */}
            <Card style={{ marginBottom: 24 }}>
              <ReactECharts
                option={getRadarOption()}
                style={{ height: '350px' }}
                opts={{ renderer: 'svg' }}
              />
            </Card>

            {/* 综合结论 */}
            <Alert
              message="黑带专家综合结论"
              description={analysisResult.conclusion}
              type={
                analysisResult.priority === 'critical' ? 'error' :
                analysisResult.priority === 'high' ? 'warning' : 'info'
              }
              showIcon
              style={{ marginBottom: 24 }}
            />

            {/* 根因分析 */}
            <Card title={<><WarningOutlined /> 根因分析</>} style={{ marginBottom: 24 }}>
              {analysisResult.rootCauses.length > 0 ? (
                <Timeline>
                  {analysisResult.rootCauses.map((rc, index) => (
                    <Timeline.Item
                      key={index}
                      color={rc.impact === 'high' ? 'red' : 'orange'}
                    >
                      <Text strong>{rc.cause}</Text>
                      <br />
                      <Text type="secondary">{rc.evidence}</Text>
                      <Tag color={rc.impact === 'high' ? 'red' : 'orange'} style={{ marginLeft: 8 }}>
                        {rc.impact === 'high' ? '高影响' : '中影响'}
                      </Tag>
                    </Timeline.Item>
                  ))}
                </Timeline>
              ) : (
                <Alert message="未发现明显异常，过程运行良好" type="success" showIcon />
              )}
            </Card>

            {/* DMAIC改进路径 */}
            <Card title={<><BulbOutlined /> DMAIC改进路径</>} style={{ marginBottom: 24 }}>
              {analysisResult.improvements && analysisResult.improvements.length > 0 ? (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  {analysisResult.improvements.map((improvement, index) => (
                    <Card
                      key={index}
                      size="small"
                      style={{
                        backgroundColor: index < 2 ? '#f6ffed' : '#fafafa',
                        borderColor: index < 2 ? '#b7eb8f' : '#d9d9d9'
                      }}
                    >
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff' }}>
                          {index < 2 && <CheckCircleOutlined style={{ marginRight: 8 }} />}
                          {improvement.phase} 阶段
                        </div>
                        <div>
                          {improvement.actions.map((action, i) => (
                            <div key={i} style={{ marginBottom: 8, fontSize: '14px', color: '#333', paddingLeft: 24 }}>
                              • {action}
                            </div>
                          ))}
                        </div>
                      </Space>
                    </Card>
                  ))}
                </Space>
              ) : (
                <Alert message="暂无改进建议" type="info" showIcon />
              )}
            </Card>

            {/* 关键问题 */}
            {analysisResult.keyProblems && analysisResult.keyProblems.length > 0 && (
              <Card title="关键问题识别 (帕累托分析)" style={{ marginBottom: 24 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {analysisResult.keyProblems.filter(p => p && p.category).map((problem, index) => (
                    <Alert
                      key={index}
                      message={`${index + 1}. ${problem.category}`}
                      description={`频次: ${problem.count || 0} | 累计占比: ${(problem.cumulative_pct || 0).toFixed(1)}%`}
                      type="warning"
                      showIcon
                    />
                  ))}
                </Space>
              </Card>
            )}

            {/* 预期收益 */}
            <Card title={<><CheckCircleOutlined /> 预期收益</>} style={{ marginBottom: 24 }}>
              <ul>
                {analysisResult.expectedBenefits.map((benefit, index) => (
                  <li key={index}>
                    <Text>{benefit}</Text>
                  </li>
                ))}
              </ul>
            </Card>

            {/* 分析时间 */}
            <div style={{ textAlign: 'right', color: '#999', fontSize: '12px' }}>
              报告生成时间: {analysisResult.analysisTime}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default IntelligentAnalysisPage;
