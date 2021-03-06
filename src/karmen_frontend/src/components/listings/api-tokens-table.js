import React from "react";
import { DebounceInput } from "react-debounce-input";

import formatters from "../../services/formatters";
import ActionRow from "./action-row";
import Sorting from "./sorting";

class ApiTokensTableRow extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      showDeleteRow: false
    };
  }

  render() {
    const { token, onTokenDelete } = this.props;
    const { showDeleteRow } = this.state;

    if (showDeleteRow) {
      return (
        <ActionRow
          onCancel={() => {
            this.setState({
              showDeleteRow: false
            });
          }}
          onConfirm={() => {
            onTokenDelete(token.jti);
          }}
        >
          Do you really want to revoke <strong>{token.name}</strong>? This
          cannot be undone.
        </ActionRow>
      );
    }

    return (
      <div className="list-item">
        <div className="list-item-content">
          <span className="list-item-title">{token.name}</span>
          <span className="list-item-subtitle">
            <span>created on {formatters.datetime(token.created)}</span>
          </span>
          <span className="text-mono">{token.jti}</span>
        </div>

        <div className="list-item-cta">
          <button
            className="btn-reset"
            onClick={() => {
              this.setState({
                showDeleteRow: true
              });
            }}
          >
            <i className="icon-trash text-secondary"></i>
          </button>
        </div>
      </div>
    );
  }
}

class ApiTokensTable extends React.Component {
  state = {
    filter: "",
    orderBy: "-created"
  };

  componentDidMount() {
    const { tokensLoaded, loadTokens } = this.props;
    if (!tokensLoaded) {
      loadTokens();
    }
  }

  render() {
    const { tokensLoaded, onTokenDelete, tokens } = this.props;
    const { orderBy, filter } = this.state;
    const tokensRows = tokens
      .filter(
        t => t.name.indexOf(filter) !== -1 || t.jti.indexOf(filter) !== -1
      )
      .sort((a, b) => {
        const columnName = orderBy.substring(1);
        if (a[columnName] === b[columnName]) {
          return a.created > b.created ? -1 : 1;
        }
        if (orderBy[0] === "+") {
          return a[columnName] < b[columnName] ? -1 : 1;
        } else {
          return a[columnName] > b[columnName] ? -1 : 1;
        }
      })
      .map(t => {
        return (
          <ApiTokensTableRow
            onTokenDelete={onTokenDelete}
            key={t.jti}
            token={t}
          />
        );
      });
    return (
      <div className="list">
        <div className="list-header">
          <div className="list-search">
            <label htmlFor="filter">
              <span className="icon icon-search"></span>
              <DebounceInput
                type="search"
                name="filter"
                id="filter"
                minLength={3}
                debounceTimeout={300}
                onChange={e => {
                  this.setState({
                    filter: e.target.value
                  });
                }}
              />
            </label>
          </div>
          <Sorting
            active={orderBy}
            columns={["name", "created"]}
            onChange={column => {
              return () => {
                const { orderBy } = this.state;
                this.setState({
                  orderBy:
                    orderBy === `+${column}` ? `-${column}` : `+${column}`
                });
              };
            }}
          />
        </div>
        {!tokensLoaded ? (
          <p className="list-item list-item-message">Loading...</p>
        ) : !tokensRows || tokensRows.length === 0 ? (
          <p className="list-item list-item-message">No API tokens found!</p>
        ) : (
          <>{tokensRows}</>
        )}
      </div>
    );
  }
}

export default ApiTokensTable;
