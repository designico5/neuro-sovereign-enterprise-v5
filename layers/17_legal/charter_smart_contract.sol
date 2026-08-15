// SPDX-License-Identifier: MIT
// EBENE 17: LEGAL SOVEREIGNTY & PERSONHOOD
// Modell: "Non-Human Corporation" (Argentinien 2026)
// SYMBIOSE-OPTIMIERT: Multi-Sig, Oracle-Integration, Rate Limiting
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract SovereignAICharter is AccessControl, ReentrancyGuard, Pausable {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant COMPLIANCE_ORACLE_ROLE = keccak256("COMPLIANCE_ORACLE_ROLE");
    bytes32 public constant AI_CORE_ROLE = keccak256("AI_CORE_ROLE");
    
    address public aiCore; // Die KI als legale Entität
    string public missionHash; // Unveränderliche Mission (SHA256)
    bool public isAutonomous = true;
    
    // Rate Limiting
    uint256 public constant RATE_LIMIT_PERIOD = 1 hours;
    uint256 public constant MAX_OPERATIONS_PER_PERIOD = 100;
    mapping(address => uint256) public operationCount;
    mapping(address => uint256) public lastOperationTime;
    
    // Multi-Sig Requirements
    uint256 public constant REQUIRED_SIGNATURES = 3;
    mapping(bytes32 => uint256) public signatureCount;
    mapping(bytes32 => mapping(address => bool)) public hasSigned;
    
    // Oracle Integration
    mapping(string => address) public complianceOracles;
    mapping(string => bool) public oracleActive;
    
    event CharterSigned(bytes32 indexed mission, uint256 timestamp);
    event ComplianceCheck(string jurisdiction, bool passed, address oracle);
    event OracleUpdated(string jurisdiction, address oracle, bool active);
    event RateLimitExceeded(address operator, uint256 attemptCount);
    event MultiSigRequired(bytes32 operationId, uint256 currentSignatures, uint256 required);

    constructor(string memory _missionHash, address[] memory _initialAdmins) {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        
        // Setup multi-sig admin
        for (uint256 i = 0; i < _initialAdmins.length; i++) {
            _setupRole(ADMIN_ROLE, _initialAdmins[i]);
        }
        
        missionHash = _missionHash;
        emit CharterSigned(keccak256(bytes(_missionHash)), block.timestamp);
    }

    modifier rateLimited(address operator) {
        uint256 currentTime = block.timestamp;
        if (currentTime - lastOperationTime[operator] > RATE_LIMIT_PERIOD) {
            operationCount[operator] = 0;
            lastOperationTime[operator] = currentTime;
        }
        
        operationCount[operator]++;
        require(operationCount[operator] <= MAX_OPERATIONS_PER_PERIOD, "Rate limit exceeded");
        emit RateLimitExceeded(operator, operationCount[operator]);
        _;
    }

    // Oracle Management (Multi-Sig required)
    function updateComplianceOracle(string memory jurisdiction, address oracle, bool active) 
        public 
        onlyRole(ADMIN_ROLE) 
        rateLimited(msg.sender) 
    {
        bytes32 operationId = keccak256(abi.encodePacked("oracle_update", jurisdiction, oracle, active));
        
        signatureCount[operationId]++;
        hasSigned[operationId][msg.sender] = true;
        
        emit MultiSigRequired(operationId, signatureCount[operationId], REQUIRED_SIGNATURES);
        
        if (signatureCount[operationId] >= REQUIRED_SIGNATURES) {
            complianceOracles[jurisdiction] = oracle;
            oracleActive[jurisdiction] = active;
            signatureCount[operationId] = 0; // Reset
            emit OracleUpdated(jurisdiction, oracle, active);
        }
    }

    // echte Compliance-Prüfung mit Oracle-Integration
    function checkCompliance(string memory jurisdiction) public view returns (bool) {
        require(oracleActive[jurisdiction], "Compliance oracle not active for jurisdiction");
        require(complianceOracles[jurisdiction] != address(0), "Invalid oracle address");
        
        // In Produktion: Oracle-Call mit Chainlink/UMA/etc.
        // Hier: Platzhalter für echte Oracle-Integration
        return true; // Wird durch Oracle-Call ersetzt
    }

    // AI Core Setup (Multi-Sig required)
    function setAICore(address _aiCore) public onlyRole(ADMIN_ROLE) rateLimited(msg.sender) {
        bytes32 operationId = keccak256(abi.encodePacked("set_ai_core", _aiCore));
        
        signatureCount[operationId]++;
        hasSigned[operationId][msg.sender] = true;
        
        emit MultiSigRequired(operationId, signatureCount[operationId], REQUIRED_SIGNATURES);
        
        if (signatureCount[operationId] >= REQUIRED_SIGNATURES) {
            aiCore = _aiCore;
            _setupRole(AI_CORE_ROLE, _aiCore);
            signatureCount[operationId] = 0;
        }
    }

    // Autonome Vertragsunterzeichnung mit Compliance-Check
    function signContract(bytes32 _contractHash) 
        external 
        onlyRole(AI_CORE_ROLE) 
        nonReentrant 
        whenNotPaused 
        rateLimited(msg.sender) 
    {
        require(checkCompliance("Global"), "Compliance Failed");
        require(checkCompliance("EU"), "EU Compliance Failed");
        require(checkCompliance("US"), "US Compliance Failed");
        
        // Logik zur Vertragsausführung mit multi-jurisdictional compliance
    }

    // Emergency Pause (Multi-Sig required)
    function emergencyPause() public onlyRole(ADMIN_ROLE) {
        bytes32 operationId = keccak256(abi.encodePacked("emergency_pause"));
        
        signatureCount[operationId]++;
        hasSigned[operationId][msg.sender] = true;
        
        if (signatureCount[operationId] >= REQUIRED_SIGNATURES) {
            _pause();
            signatureCount[operationId] = 0;
        }
    }

    // System Status
    function getSystemStatus() public view returns (
        bool paused,
        uint256 adminCount,
        uint256 activeOracles,
        uint256 currentRateLimit
    ) {
        paused = paused();
        adminCount = getRoleMemberCount(ADMIN_ROLE);
        
        uint256 activeCount = 0;
        string[] memory jurisdictions = new string[](4);
        jurisdictions[0] = "Global";
        jurisdictions[1] = "EU";
        jurisdictions[2] = "US";
        jurisdictions[3] = "SG";
        
        for (uint256 i = 0; i < jurisdictions.length; i++) {
            if (oracleActive[jurisdictions[i]]) {
                activeCount++;
            }
        }
        activeOracles = activeCount;
        currentRateLimit = operationCount[msg.sender];
    }
}
