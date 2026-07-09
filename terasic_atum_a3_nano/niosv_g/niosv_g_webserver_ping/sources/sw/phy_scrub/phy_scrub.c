typedef unsigned short u16;
typedef unsigned int u32;

#define TSE_BASE 0x04090400u
#define MDIO0_OFFSET 0x200u
#define PHY_REG(reg) ((volatile u16 *)(TSE_BASE + MDIO0_OFFSET + ((reg) * 4u)))

#define BMCR 0x00u
#define BISCR 0x16u
#define REGCR 0x0du
#define ADDAR 0x0eu

#define BMCR_RESET (1u << 15)
#define BMCR_LOOPBACK (1u << 14)
#define REGCR_DATA_NO_POST_INC 0x4000u
#define DP83867_DEVADDR 0x001fu
#define DP83867_LOOPCR 0x00feu
#define DP83867_LOOPCR_NORMAL 0xe721u
#define BISCR_LOOPBACK_MODE_MASK ((1u << 5) | (1u << 6))

static void delay(volatile u32 count)
{
    while (count-- != 0u) {
        __asm__ volatile("nop");
    }
}

static u16 phy_read(u32 reg)
{
    return *PHY_REG(reg);
}

static void phy_write(u32 reg, u16 value)
{
    *PHY_REG(reg) = value;
    delay(10000u);
}

static void mmd_write(u16 reg, u16 value)
{
    phy_write(REGCR, DP83867_DEVADDR);
    phy_write(ADDAR, reg);
    phy_write(REGCR, REGCR_DATA_NO_POST_INC | DP83867_DEVADDR);
    phy_write(ADDAR, value);
}

void _start(void)
{
    u16 bmcr;
    u16 biscr;

    phy_write(BMCR, BMCR_RESET);
    delay(5000000u);

    bmcr = phy_read(BMCR);
    bmcr &= (u16)~BMCR_LOOPBACK;
    phy_write(BMCR, bmcr);

    biscr = phy_read(BISCR);
    biscr &= (u16)~BISCR_LOOPBACK_MODE_MASK;
    phy_write(BISCR, biscr);

    mmd_write(DP83867_LOOPCR, DP83867_LOOPCR_NORMAL);

    for (;;) {
        __asm__ volatile("wfi");
    }
}
