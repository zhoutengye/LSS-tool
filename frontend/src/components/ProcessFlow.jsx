import { useState, useCallback, useEffect } from 'react';
import ReactFlow, { 
  Controls, 
  Background, 
  applyEdgeChanges, 
  applyNodeChanges, 
  addEdge 
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Modal, Form, InputNumber, message, Button, Tag } from 'antd';
import axios from 'axios';

export default function ProcessFlow() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [expandedBlocks, setExpandedBlocks] = useState(new Set()); // 记录哪些区块已展开

  // 🚀 组件加载时，去后端拿图谱
  useEffect(() => {
    axios.get('http://127.0.0.1:8000/api/graph/structure')
      .then(res => {
        // 过滤掉初始隐藏的节点
        const visibleNodes = res.data.nodes.filter(n => !n.hidden);
        const visibleEdges = res.data.edges.filter(e => !e.hidden);
        setNodes(visibleNodes);
        setEdges(visibleEdges);
      })
      .catch(err => {
        console.error('获取图谱失败:', err);
        message.error('无法加载流程图数据');
      });
  }, []);
  
  // 弹窗状态
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingNode, setEditingNode] = useState(null);
  const [form] = Form.useForm();

  // React Flow 基础回调
  const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), []);

  // 点击区块：展开/折叠
  const onNodeClick = useCallback((event, node) => {
    console.log('点击节点:', node); // 调试日志

    if (node.data.type === 'Block') {
      const isExpanded = expandedBlocks.has(node.id);
      console.log('区块展开状态:', isExpanded); // 调试日志
      const newExpanded = new Set(expandedBlocks);

      if (isExpanded) {
        // 折叠：移除该区块的所有子节点
        console.log('折叠区块'); // 调试日志
        newExpanded.delete(node.id);
        setNodes((nds) => nds.filter(n => n.data.parentId !== node.id));
        setEdges((eds) => eds.filter(e => {
          const sourceNode = nodes.find(n => n.id === e.source);
          const targetNode = nodes.find(n => n.id === e.target);
          return sourceNode?.data.parentId !== node.id && targetNode?.data.parentId !== node.id;
        }));
      } else {
        // 展开：添加该区块的所有子节点
        console.log('展开区块:', node.id); // 调试日志
        newExpanded.add(node.id);

        // 重新获取所有节点数据
        axios.get('http://127.0.0.1:8000/api/graph/structure')
          .then(res => {
            console.log('API返回节点数:', res.data.nodes.length); // 调试日志
            const childNodes = res.data.nodes.filter(n => n.data.parentId === node.id);
            console.log('子节点数:', childNodes.length); // 调试日志

            // 只添加子节点之间的连线，不包括区块间的主流程连线
            const childEdges = res.data.edges.filter(e => {
              // 排除区块间的主流程连线（它们的 ID 以 block_edge_ 开头）
              if (e.id && e.id.startsWith('block_edge_')) {
                return false;
              }

              const sourceNode = res.data.nodes.find(n => n.id === e.source);
              const targetNode = res.data.nodes.find(n => n.id === e.target);
              return (sourceNode?.data.parentId === node.id ||
                targetNode?.data.parentId === node.id);
            });

            // 计算子节点位置（垂直排列）
            let yOffset = 200;
            const positionedNodes = childNodes.map((n, idx) => ({
              ...n,
              position: { x: node.position.x, y: yOffset + idx * 150 },
              hidden: false,  // 重要：移除 hidden 标记，让节点可见
              data: {
                ...n.data,
                hidden: false  // 同时移除 data 里的 hidden
              }
            }));

            const visibleEdges = childEdges.map(e => ({
              ...e,
              hidden: false  // 移除边的 hidden 标记
            }));

            console.log('添加子节点:', positionedNodes.length); // 调试日志
            console.log('子节点示例:', positionedNodes[0]); // 调试日志
            setNodes((nds) => [...nds, ...positionedNodes]);
            setEdges((eds) => {
              // 只添加不存在的边，避免重复
              const existingEdgeIds = new Set(eds.map(e => e.id));
              const newEdges = visibleEdges.filter(e => !existingEdgeIds.has(e.id));
              console.log('添加新边数:', newEdges.length); // 调试日志
              return [...eds, ...newEdges];
            });
          })
          .catch(err => console.error('展开失败:', err));
      }

      setExpandedBlocks(newExpanded);
    }
  }, [expandedBlocks]);

  // 双击节点：打开设置弹窗（只对 Unit 节点）
  const onNodeDoubleClick = (event, node) => {
    // 区块节点不打开弹窗
    if (node.data.type === 'Block') {
      return;
    }

    console.log('双击节点:', node); // 调试日志
    setEditingNode(node);

    // 如果节点有参数定义，动态生成表单字段
    if (node.data.params && node.data.params.length > 0) {
      const initialValues = {};
      node.data.params.forEach(param => {
        // 使用 target 值作为默认值，如果没有则用 0
        initialValues[param.code] = param.target !== undefined ? param.target : 0;
      });
      form.setFieldsValue(initialValues);
    }

    setIsModalOpen(true);
  };

  // 点击确定：调用后端仿真接口
  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      
      // 🚀 核心：调用 Python 后端
      const res = await axios.post('http://127.0.0.1:8000/api/simulate', {
        temperature: values.temperature
      });

      const { result_yield } = res.data;

      // 更新节点显示
      setNodes((nds) => nds.map((node) => {
        if (node.id === editingNode.id) {
          // 如果得率太低(<90)，把框变红
          const color = result_yield < 90 ? 'red' : '#1890ff';
          node.style = { ...node.style, borderColor: color, borderWidth: 2 };
          node.data = { ...node.data, ...values, label: `${node.data.label}\n得率: ${result_yield}%` };
          
          if (result_yield < 90) message.warning(`警告：仿真得率仅为 ${result_yield}%`);
          else message.success(`仿真成功：得率 ${result_yield}%`);
        }
        return node;
      }));

      setIsModalOpen(false);
    } catch (err) {
      message.error('连接后端失败');
      console.error(err);
    }
  };

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onNodeDoubleClick={onNodeDoubleClick}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>

      <Modal
        title={`🔧 工艺参数配置 - ${editingNode?.data?.label || ''}`}
        open={isModalOpen}
        onOk={handleOk}
        onCancel={() => setIsModalOpen(false)}
        width={600}
      >
        {editingNode?.data?.params && editingNode.data.params.length > 0 ? (
          <Form form={form} layout="vertical">
            {editingNode.data.params.map(param => (
              <Form.Item
                key={param.code}
                name={param.code}
                label={
                  <span>
                    {param.name || param.code} ({param.unit || ''})
                    {param.role === 'Control' && <Tag color="blue" style={{ marginLeft: 8 }}>控制</Tag>}
                    {param.role === 'Output' && <Tag color="green" style={{ marginLeft: 8 }}>输出</Tag>}
                    {param.role === 'Input' && <Tag color="orange" style={{ marginLeft: 8 }}>输入</Tag>}
                  </span>
                }
                extra={
                  (param.usl !== null && param.usl !== undefined) || (param.lsl !== null && param.lsl !== undefined) ? (
                    <span style={{ color: '#666', fontSize: '12px' }}>
                      规格范围: {param.lsl ?? '-'} ~ {param.usl ?? '-'}
                      {param.target !== null && param.target !== undefined && ` (目标: ${param.target})`}
                    </span>
                  ) : null
                }
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder={`输入${param.name}`}
                  disabled={param.role === 'Output'} // 输出参数不可编辑
                />
              </Form.Item>
            ))}
          </Form>
        ) : (
          <p>此节点暂无可配置参数</p>
        )}
      </Modal>
    </div>
  );
}
