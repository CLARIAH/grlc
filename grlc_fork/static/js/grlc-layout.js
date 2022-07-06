// Create the layout component
class GrlcLayout extends React.Component {
  render() {
    const {
      getComponent
    } = this.props;

    const BaseLayout = getComponent("BaseLayout", true);

    // layoutJSX is the compiled version of JSX code:
    // (<div><BaseLayout /></div>)
    // Compiled using babeljs.io as suggested by https://reactjs.org/docs/react-without-jsx.html
    const layoutJSX = React.createElement(
      "div", null,
      React.createElement(BaseLayout, null)
    );
    return layoutJSX;
  }
}

// Create the plugin that provides our layout component
const GrlcLayoutPlugin = () => {
  return {
    components: {
      GrlcLayout: GrlcLayout
    }
  }
}
