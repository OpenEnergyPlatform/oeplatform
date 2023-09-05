import React, { Component } from "react";
import TreeView from '@material-ui/lab/TreeView';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import TreeItem from '@material-ui/lab/TreeItem';

class CustomTreeView extends Component {
  constructor(props) {
    super(props);

    this.handleToggle = this.handleToggle.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.treeViewSelectHandler = this.props.treeViewSelectHandler.bind(this);
    this.state = {
      expanded: this.props.expanded,
      selected: this.props.selected,
      treeViewData: this.props.treeViewData,
      treeViewSelectHandler: this.props.treeViewSelectHandler
    }
  }

   componentDidUpdate(prevProps){
     if (this.props.expanded !== prevProps.expanded) {
        this.setState({
          expanded: this.props.expanded,
        });
      }
  };

  handleToggle(event, nodeIds) {
    this.setState({
      expanded: nodeIds,
    });
  };

  handleSelect(event, nodeId) {
    this.state.treeViewSelectHandler(event, nodeId);
  };


  render() {
    const renderTree = (nodes) => (
    <TreeItem key={nodes.id} nodeId={nodes.id} label={nodes.name}>
      {Array.isArray(nodes.children) ? nodes.children.map((node) => renderTree(node)) : null}
    </TreeItem>
    );
    return (
        <div style={{ height: '75%', maxHeight: '700px' }}>
          <TreeView
            defaultCollapseIcon={<ExpandMoreIcon />}
            defaultExpandIcon={<ChevronRightIcon />}
            expanded={this.state.expanded}
            onNodeToggle={this.handleToggle}
            onNodeSelect={this.handleSelect}
          >
            {renderTree(this.state.treeViewData)}
          </TreeView>
       </div>
    );
  }
}

export default CustomTreeView;
