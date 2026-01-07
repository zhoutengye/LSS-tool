import { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Button,
  Select,
  Space,
  Alert,
  Spin,
  message,
  Row,
  Col,
  Typography,
  Divider,
  Tag
} from 'antd';
import {
  BarChartOutlined,
  LineChartOutlined,
  PlayCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import axios from 'axios';
import ParetoChart from '../components/lss/ParetoChart';
import HistogramChart from '../components/lss/HistogramChart';
import BoxplotChart from '../components/lss/BoxplotChart';
import SPCChart from '../components/lss/SPCChart';

const { TabPane } = Tabs;
const { Option } = Select;
const { Title, Paragraph, Text } = Typography;

/**
 * LSS工具箱演示页面
 *
 * 提供4个主要LSS工具的可视化演示：
 * 1. 帕累托图 - 识别关键问题
 * 2. 直方图 - 分析分布形态
 * 3. 箱线图 - 多组对比
 * 4. SPC控制图 - 过程能力分析
 */
const LSSToolsPage = () => {
  // 状态管理
  const [activeTab, setActiveTab] = useState('pareto');
  const [loading, setLoading] = useState(false);
  const [paretoResult, setParetoResult] = useState(null);
  const [histogramResult, setHistogramResult] = useState(null);
  const [boxplotResult, setBoxplotResult] = useState(null);
  const [spcResult, setSpcResult] = useState(null);

  // 参数选择状态
  const [selectedParam, setSelectedParam] = useState('P_E01_TEMP');
  const [selectedNode, setSelectedNode] = useState('E01');

  // 获取演示场景
  const [scenarios, setScenarios] = useState([]);

  // 加载演示场景
  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8000/api/lss/demo/scenarios');
      if (res.data.success) {
        setScenarios(res.data.scenarios);
      }
    } catch (error) {
      console.error('获取演示场景失败:', error);
    }
  };

  // 帕累托图分析
  const runParetoAnalysis = async () => {
    setLoading(true);
    try {
      // 先获取演示数据
      const demoRes = await axios.get('http://127.0.0.1:8000/api/lss/pareto/demo');

      if (demoRes.data.success) {
        // 运行分析
        const analysisRes = await axios.post(
          'http://127.0.0.1:8000/api/lss/pareto/analyze',
          {
            categories: demoRes.data.data,
            threshold: 0.8
          }
        );

        if (analysisRes.data.success) {
          setParetoResult(analysisRes.data);
          message.success('帕累托图分析完成');
        } else {
          message.error('分析失败: ' + (analysisRes.data.errors?.join(', ') || '未知错误'));
        }
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 直方图分析
  const runHistogramAnalysis = async () => {
    setLoading(true);
    try {
      const res = await axios.post('http://127.0.0.1:8000/api/lss/histogram/analyze', {
        param_code: selectedParam,
        node_code: selectedNode,
        limit: 100,
        bins: 10
      });

      if (res.data.success) {
        setHistogramResult(res.data);
        message.success('直方图分析完成');
      } else {
        message.error('分析失败: ' + (res.data.errors?.join(', ') || '未知错误'));
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 箱线图分析
  const runBoxplotAnalysis = async () => {
    setLoading(true);
    try {
      // 先获取演示配置
      const demoRes = await axios.get('http://127.0.0.1:8000/api/lss/boxplot/demo');

      if (demoRes.data.success) {
        // 运行分析
        const analysisRes = await axios.post(
          'http://127.0.0.1:8000/api/lss/boxplot/analyze',
          {
            param_codes: demoRes.data.config.param_codes,
            limit_per_series: 50
          }
        );

        if (analysisRes.data.success) {
          setBoxplotResult(analysisRes.data);
          message.success('箱线图分析完成');
        } else {
          message.error('分析失败: ' + (analysisRes.data.errors?.join(', ') || '未知错误'));
        }
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // SPC分析
  const runSPCAnalysis = async () => {
    setLoading(true);
    try {
      const res = await axios.post('http://127.0.0.1:8000/api/lss/spc/analyze', {
        param_code: selectedParam,
        node_code: selectedNode,
        limit: 50
      });

      if (res.data.success) {
        setSpcResult(res.data);
        message.success('SPC分析完成');
      } else {
        message.error('分析失败: ' + (res.data.errors?.join(', ') || '未知错误'));
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 快速演示 - 运行所有分析
  const runAllDemo = async () => {
    message.info('开始运行所有LSS工具分析...');
    await Promise.all([
      runParetoAnalysis(),
      runHistogramAnalysis(),
      runBoxplotAnalysis(),
      runSPCAnalysis()
    ]);
    message.success('所有分析完成！');
  };

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      {/* 页面标题 */}
      <Card style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              📊 LSS 工具箱演示
            </Title>
            <Paragraph type="secondary" style={{ marginTop: 8 }}>
              精益六西格玛（Lean Six Sigma）分析工具集 - 基于真实数据的可视化分析
            </Paragraph>
          </div>

          {/* 快速操作 */}
          <Row gutter={16}>
            <Col span={12}>
              <Space>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  size="large"
                  onClick={runAllDemo}
                >
                  快速演示（运行所有工具）
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => {
                    setParetoResult(null);
                    setHistogramResult(null);
                    setBoxplotResult(null);
                    setSpcResult(null);
                    message.info('已清除所有分析结果');
                  }}
                >
                  清除结果
                </Button>
              </Space>
            </Col>
            <Col span={12} style={{ textAlign: 'right' }}>
              <Space>
                <Text type="secondary">参数: </Text>
                <Select
                  value={selectedParam}
                  onChange={setSelectedParam}
                  style={{ width: 150 }}
                >
                  <Option value="P_E01_TEMP">E01温度</Option>
                  <Option value="P_C01_TEMP">C01温度</Option>
                  <Option value="P_E01_PRESSURE">E01压力</Option>
                </Select>
                <Text type="secondary">节点: </Text>
                <Select
                  value={selectedNode}
                  onChange={setSelectedNode}
                  style={{ width: 100 }}
                >
                  <Option value="E01">E01</Option>
                  <Option value="C01">C01</Option>
                  <Option value="E02">E02</Option>
                </Select>
              </Space>
            </Col>
          </Row>

          {/* 演示场景 */}
          {scenarios.length > 0 && (
            <div>
              <Divider orientation="left">演示场景</Divider>
              <Row gutter={16}>
                {scenarios.map(scenario => (
                  <Col span={6} key={scenario.id}>
                    <Card
                      size="small"
                      hoverable
                      onClick={() => {
                        setActiveTab(scenario.tool);
                        // 根据场景运行对应分析
                        setTimeout(() => {
                          if (scenario.tool === 'pareto') runParetoAnalysis();
                          else if (scenario.tool === 'histogram') runHistogramAnalysis();
                          else if (scenario.tool === 'boxplot') runBoxplotAnalysis();
                          else if (scenario.tool === 'spc') runSPCAnalysis();
                        }, 100);
                      }}
                      style={{ cursor: 'pointer' }}
                    >
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '24px', marginBottom: 8 }}>
                          {scenario.tool === 'pareto' && <BarChartOutlined />}
                          {scenario.tool === 'histogram' && <BarChartOutlined />}
                          {scenario.tool === 'boxplot' && <BarChartOutlined />}
                          {scenario.tool === 'spc' && <LineChartOutlined />}
                        </div>
                        <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                          {scenario.name}
                        </div>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          {scenario.description}
                        </div>
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>
          )}
        </Space>
      </Card>

      {/* 工具选项卡 */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          size="large"
          tabBarExtraContent={
            <Space>
              <Tag color="blue">4个工具</Tag>
              <Tag color="green">真实数据</Tag>
            </Space>
          }
        >
          {/* 帕累托图 */}
          <TabPane
            tab={
              <span>
                <BarChartOutlined />
                帕累托图分析
              </span>
            }
            key="pareto"
          >
            <Card
              title="QA质量分析会 - 识别关键问题"
              extra={
                <Button type="primary" onClick={runParetoAnalysis} loading={loading}>
                  运行分析
                </Button>
              }
            >
              <Alert
                message="应用场景"
                description="在QA质量分析会上，通过帕累托图展示故障类别分布，快速识别出需要优先解决的'关键少数'问题（80/20法则）。"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Spin spinning={loading}>
                <ParetoChart result={paretoResult} loading={loading} />
              </Spin>
            </Card>
          </TabPane>

          {/* 直方图 */}
          <TabPane
            tab={
              <span>
                <BarChartOutlined />
                直方图分析
              </span>
            }
            key="histogram"
          >
            <Card
              title="工艺参数调优 - 分析分布形态"
              extra={
                <Button type="primary" onClick={runHistogramAnalysis} loading={loading}>
                  运行分析
                </Button>
              }
            >
              <Alert
                message="应用场景"
                description="在工艺优化过程中，通过直方图分析参数分布形态，检验正态性，计算过程能力，识别需要改进的工艺环节。"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Spin spinning={loading}>
                <HistogramChart result={histogramResult} loading={loading} />
              </Spin>
            </Card>
          </TabPane>

          {/* 箱线图 */}
          <TabPane
            tab={
              <span>
                <BarChartOutlined />
                箱线图分析
              </span>
            }
            key="boxplot"
          >
            <Card
              title="车间对比会 - 识别最佳实践"
              extra={
                <Button type="primary" onClick={runBoxplotAnalysis} loading={loading}>
                  运行分析
                </Button>
              }
            >
              <Alert
                message="应用场景"
                description="在车间对比会议上，通过箱线图对比多个车间的过程波动，识别出最佳实践车间和需要改进的问题车间。"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Spin spinning={loading}>
                <BoxplotChart result={boxplotResult} loading={loading} />
              </Spin>
            </Card>
          </TabPane>

          {/* SPC控制图 */}
          <TabPane
            tab={
              <span>
                <LineChartOutlined />
                SPC过程能力分析
              </span>
            }
            key="spc"
          >
            <Card
              title="日常监控 - 过程能力评估"
              extra={
                <Button type="primary" onClick={runSPCAnalysis} loading={loading}>
                  运行分析
                </Button>
              }
            >
              <Alert
                message="应用场景"
                description="在日常生产监控中，通过SPC控制图实时监控过程参数，计算过程能力指数（Cpk），及时发现异常并预警。"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Spin spinning={loading}>
                <SPCChart result={spcResult} loading={loading} />
              </Spin>
            </Card>
          </TabPane>
        </Tabs>
      </Card>

      {/* 页脚说明 */}
      <Card style={{ marginTop: 24, textAlign: 'center', background: '#f9f9f9' }}>
        <Space direction="vertical" size="small">
          <Text type="secondary">
            LSS Engine v2.0 - 精益六西格玛智能分析系统
          </Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            数据来源: 真实生产数据库 | 工具数量: 4 | 演示场景: {scenarios.length}
          </Text>
        </Space>
      </Card>
    </div>
  );
};

export default LSSToolsPage;
