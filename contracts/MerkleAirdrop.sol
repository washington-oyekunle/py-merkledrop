// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title MerkleAirdrop
 * @notice Minimal Merkle airdrop claim contract. Compatible with py-merkledrop roots (SHA256).
 *         Adjust hashing to keccak256 if desired for gas savings.
 */
contract MerkleAirdrop {
    bytes32 public immutable root;
    address public immutable token;
    mapping(address => bool) public claimed;

    event Claimed(address indexed account, uint256 amount);

    constructor(bytes32 _root, address _token) {
        root = _root;
        token = _token;
    }

    function claim(uint256 amount, bytes32[] calldata proof) external {
        require(!claimed[msg.sender], "Already claimed");
        require(_verify(msg.sender, amount, proof), "Invalid proof");

        claimed[msg.sender] = true;
        // IERC20(token).transfer(msg.sender, amount);  // Uncomment and import when ready
        emit Claimed(msg.sender, amount);
    }

    function _verify(address account, uint256 amount, bytes32[] calldata proof) internal view returns (bool) {
        bytes32 leaf = sha256(abi.encodePacked(account, amount));
        bytes32 computed = leaf;

        for (uint256 i = 0; i < proof.length; i++) {
            bytes32 sibling = proof[i];
            if (computed > sibling) {
                (computed, sibling) = (sibling, computed);
            }
            computed = sha256(abi.encodePacked(computed, sibling));
        }
        return computed == root;
    }
}
